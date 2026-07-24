#!/bin/bash
# ═══════════════════════════════════════════════
# Deploy CRM Corsi (bot Telegram) su VPS Hostinger
# Uso: ./deploy-crm-corsi.sh
#
# Segue lo stesso schema di deploy-portalecse.sh, con una differenza
# voluta: token/chiavi NON sono scritti in questo file (che finisce su
# git). Il primo avvio te li chiede a voce e li salva solo nel .env
# locale sulla VPS, mai nel repository.
# ═══════════════════════════════════════════════

set -e

APP_NAME="crm-corsi"
APP_PORT="8022"
DB_PORT="5440"
DOMAIN="corsibot.safetyprosuite.com"
APP_DIR="/opt/crm-corsi"
REPO_DIR="$APP_DIR/repo"
REPO_URL="https://github.com/aqrgroup/prova.git"
# Cambia in "main" una volta che il branch e' stato unito.
REPO_BRANCH="claude/crm-app-document-extraction-196mrk"
DB_CONTAINER="${APP_NAME}-db"
APP_CONTAINER="${APP_NAME}-app"
DB_NAME="crmcorsi"
DB_USER="crmcorsi"
DB_PASSWORD="$(openssl rand -hex 16)"
TELEGRAM_WEBHOOK_SECRET="$(openssl rand -hex 16)"

echo "════════════════════════════════════════════════"
echo "  DEPLOY CRM CORSI"
echo "════════════════════════════════════════════════"
echo ""
echo "  App:      $APP_NAME"
echo "  Porta:    $APP_PORT"
echo "  DB Porta: $DB_PORT"
echo "  Dominio:  $DOMAIN"
echo ""

# ─── STEP 0: Verifica porte libere ──────────────
echo "--- Step 0: Verifica porte libere ---"
if ss -ltn 2>/dev/null | grep -q ":${APP_PORT} "; then
    echo "ERRORE: la porta ${APP_PORT} e' gia' occupata."
    echo "   Modifica APP_PORT in questo script (vedi COME_USARE.md per le porte occupate) e riprova."
    exit 1
fi
if ss -ltn 2>/dev/null | grep -q ":${DB_PORT} "; then
    echo "ERRORE: la porta ${DB_PORT} e' gia' occupata."
    echo "   Modifica DB_PORT in questo script e riprova."
    exit 1
fi
echo "OK Porte libere"
echo ""

# ─── STEP 1: Crea directory progetto ────────────
echo "--- Step 1: Directory progetto ---"
mkdir -p "$APP_DIR"
echo "OK Directory $APP_DIR pronta"
echo ""

# ─── STEP 2: Database PostgreSQL ────────────────
echo "--- Step 2: Database PostgreSQL ---"
if docker ps -a --format "{{.Names}}" | grep -q "^${DB_CONTAINER}$"; then
    echo "OK Database container gia esistente"
    if ! docker ps --format "{{.Names}}" | grep -q "^${DB_CONTAINER}$"; then
        docker start "$DB_CONTAINER"
        echo "OK Database avviato"
    fi
    DB_PASSWORD=$(docker exec "$DB_CONTAINER" sh -c 'echo $POSTGRES_PASSWORD')
else
    echo "Creazione database..."
    docker run -d \
        --name "$DB_CONTAINER" \
        --network dokploy-network \
        --restart unless-stopped \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -v crm-corsi-pgdata:/var/lib/postgresql/data \
        -p ${DB_PORT}:5432 \
        postgres:15-alpine

    sleep 5
    echo "OK Database creato"
fi

docker network connect dokploy-network "$DB_CONTAINER" 2>/dev/null || true
echo ""

# ─── STEP 3: Codice sorgente ────────────────────
echo "--- Step 3: Codice sorgente ---"
if [ -d "$REPO_DIR/.git" ]; then
    echo "Repository gia' presente, aggiorno..."
    git -C "$REPO_DIR" fetch origin "$REPO_BRANCH"
    git -C "$REPO_DIR" checkout "$REPO_BRANCH"
    git -C "$REPO_DIR" pull origin "$REPO_BRANCH"
else
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
fi
echo "OK Codice aggiornato"
echo ""

# ─── STEP 4: File .env (secrets NON su git) ─────
echo "--- Step 4: Configurazione .env ---"
if [ -f "$APP_DIR/.env" ]; then
    echo "OK File .env gia esistente (non sovrascritto)"
else
    echo "Inserisci il token del bot Telegram (da @BotFather):"
    read -r TELEGRAM_BOT_TOKEN_INPUT
    echo "Inserisci la chiave Anthropic dedicata a questo bot (da console.anthropic.com):"
    read -r ANTHROPIC_API_KEY_INPUT

    cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_CONTAINER}:5432/${DB_NAME}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN_INPUT}
TELEGRAM_WEBHOOK_SECRET=${TELEGRAM_WEBHOOK_SECRET}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_INPUT}
EOF
    chmod 600 "$APP_DIR/.env"
    echo "OK File .env creato (permessi ristretti, solo root puo' leggerlo)"
fi
echo ""

# ─── STEP 5: Build immagine Docker ──────────────
echo "--- Step 5: Build immagine Docker ---"
docker build -t ${APP_NAME}:latest "$REPO_DIR/backend" 2>&1 | tail -5
echo "OK Immagine buildata"
echo ""

# ─── STEP 6: Stop container vecchio ─────────────
echo "--- Step 6: Stop container vecchio ---"
if docker ps -a --format "{{.Names}}" | grep -q "^${APP_CONTAINER}$"; then
    docker stop "$APP_CONTAINER" 2>/dev/null || true
    docker rm "$APP_CONTAINER" 2>/dev/null || true
    echo "OK Container vecchio rimosso"
else
    echo "   Nessun container vecchio"
fi
echo ""

# ─── STEP 7: Avvio container ────────────────────
echo "--- Step 7: Avvio nuovo container ---"
docker run -d \
    --name "$APP_CONTAINER" \
    --network dokploy-network \
    --restart unless-stopped \
    -p ${APP_PORT}:8000 \
    --env-file "$APP_DIR/.env" \
    ${APP_NAME}:latest

sleep 5
echo "OK Container avviato (le tabelle del database vengono create automaticamente al primo avvio)"
echo ""

# ─── STEP 8: Nginx ───────────────────────────────
echo "--- Step 8: Configurazione Nginx ---"

cat > /etc/nginx/sites-available/$DOMAIN << NGINX
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Upload foto documenti
        client_max_body_size 20M;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

if nginx -t 2>&1 | grep -q "successful"; then
    systemctl reload nginx
    echo "OK Nginx configurato e ricaricato"
else
    echo "ERRORE configurazione Nginx!"
    nginx -t
    exit 1
fi
echo ""

# ─── STEP 9: SSL ─────────────────────────────────
echo "--- Step 9: Certificato SSL ---"
if command -v certbot &> /dev/null; then
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email info@safetyprosuite.com --redirect 2>&1 | grep -E '(Successfully|Congratulations|Certificate not yet|error)' || true
    echo "OK SSL configurato"
else
    echo "ATTENZIONE: Certbot non installato"
fi
echo ""

# ─── STEP 10: Registra il webhook Telegram ──────
echo "--- Step 10: Registrazione webhook Telegram ---"
source "$APP_DIR/.env"
WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -d "url=https://${DOMAIN}/webhook/telegram" \
    -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}")
echo "$WEBHOOK_RESPONSE"
echo ""

# ─── STEP 11: Monitor Telegram (infrastruttura) ─
echo "--- Step 11: Monitor Telegram ---"
MONITOR_FILE="/opt/monitor/vps-monitor.sh"
if [ -f "$MONITOR_FILE" ]; then
    if ! grep -q "$APP_CONTAINER" "$MONITOR_FILE"; then
        sed -i "/^APPS=(/a\\    \"${APP_CONTAINER}:${APP_PORT}:${DOMAIN}\"" "$MONITOR_FILE"
        echo "OK Aggiunto al monitor Telegram (@safetypro_monitor_bot)"
    else
        echo "OK Gia presente nel monitor"
    fi
else
    echo "   Monitor non trovato"
fi
echo ""

# ─── STEP 12: Verifica finale ───────────────────
echo "--- Step 12: Verifica finale ---"
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${APP_PORT}/health" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "OK App risponde (HTTP $HTTP_STATUS)"
else
    echo "ATTENZIONE: App HTTP $HTTP_STATUS — controllare i log:"
    echo "   docker logs $APP_CONTAINER --tail 30"
fi

HTTPS_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "https://${DOMAIN}/health" 2>/dev/null || echo "000")
if [ "$HTTPS_STATUS" != "000" ]; then
    echo "OK HTTPS raggiungibile ($HTTPS_STATUS)"
else
    echo "   HTTPS non ancora raggiungibile (DNS in propagazione?)"
fi
echo ""

# ─── RIEPILOGO ───────────────────────────────────
echo "════════════════════════════════════════════════"
echo "  DEPLOY COMPLETATO!"
echo "════════════════════════════════════════════════"
echo ""
echo "  Bot Telegram: scrivi al bot su t.me/Aqr_Corsi_bot per iniziare"
echo "  App:          docker logs $APP_CONTAINER -f"
echo "  DB:           $DB_CONTAINER (porta $DB_PORT)"
echo "  Codice:       $REPO_DIR"
echo ""
echo "  Comandi utili:"
echo "    docker logs $APP_CONTAINER -f"
echo "    docker restart $APP_CONTAINER"
echo ""
echo "  Aggiornare (dopo nuove modifiche al codice):"
echo "    cd $REPO_DIR && git pull"
echo "    docker build -t ${APP_NAME}:latest $REPO_DIR/backend"
echo "    docker stop $APP_CONTAINER && docker rm $APP_CONTAINER"
echo "    docker run -d --name $APP_CONTAINER --network dokploy-network --restart unless-stopped -p ${APP_PORT}:8000 --env-file $APP_DIR/.env ${APP_NAME}:latest"
echo ""
echo "════════════════════════════════════════════════"
