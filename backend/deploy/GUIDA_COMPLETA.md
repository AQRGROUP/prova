# Guida completa: dal codice al bot online

Tutto il codice è già su GitHub, sul branch `claude/crm-app-document-extraction-196mrk`
del repository `aqrgroup/prova`. Questa guida copre: scaricarlo in VS Code,
collegarti alla VPS da lì, e mandare online il bot.

## 1. Cos'è questo progetto

Un bot Telegram (`@Aqr_Corsi_bot`) per il commerciale: raccoglie dati
azienda/lavoratori (anche da foto di documenti/visura), calcola quali corsi
servono per ogni mansione, e genera il file da caricare sulla piattaforma
corsi. Tutto il dettaglio tecnico è in `backend/README.md`.

## 2. Scaricare il codice in VS Code

Se non li hai già installati: [VS Code](https://code.visualstudio.com/) e
[Git](https://git-scm.com/downloads).

In VS Code:
1. `Ctrl+Shift+P` (o `Cmd+Shift+P` su Mac) → scrivi **"Git: Clone"** → invio
2. Incolla l'URL: `https://github.com/aqrgroup/prova.git`
3. Scegli una cartella locale dove salvarlo
4. Quando richiesto, apri la cartella clonata
5. In basso a sinistra in VS Code, sul nome del branch, clicca e seleziona
   **`claude/crm-app-document-extraction-196mrk`** (per essere sicuro di
   essere sul branch giusto)

In alternativa da terminale:
```bash
git clone https://github.com/aqrgroup/prova.git
cd prova
git checkout claude/crm-app-document-extraction-196mrk
code .
```

Il codice del bot è nella cartella `backend/`.

## 3. Collegarti alla VPS direttamente da VS Code

1. Installa l'estensione **"Remote - SSH"** di Microsoft (icona a blocchetti
   a sinistra in VS Code → cerca "Remote - SSH" → Installa)
2. `Ctrl+Shift+P` → **"Remote-SSH: Connect to Host..."** → **"Add New SSH Host..."**
3. Scrivi: `root@72.61.189.136` → invio → scegli il file di configurazione
   SSH proposto di default
4. Riapri la Command Palette → **"Remote-SSH: Connect to Host..."** → scegli
   `72.61.189.136` dalla lista
5. Si apre una nuova finestra VS Code **collegata alla VPS**: inserisci la
   password (o usa la tua chiave SSH se già configurata)
6. Apri un terminale dentro questa finestra: menu **Terminal → New Terminal**

Da qui i comandi che digiti girano davvero sulla VPS, non sul tuo PC.

## 4. Cosa tenere pronto prima del deploy

- **Token bot Telegram**: quello ottenuto da @BotFather per `@Aqr_Corsi_bot`
  (te lo sei già segnato in chat quando l'hai creato)
- **Chiave Anthropic dedicata**: creala su console.anthropic.com → Settings
  → API Keys → Create Key (se non l'hai ancora fatto)
- **DNS**: già fatto — `corsibot.safetyprosuite.com` → `72.61.189.136`

## 5. Eseguire il deploy

Nel terminale VS Code collegato alla VPS (vedi punto 3), incolla tutto
insieme:

```bash
mkdir -p /opt/crm-corsi && \
curl -o /opt/crm-corsi/deploy-crm-corsi.sh https://raw.githubusercontent.com/aqrgroup/prova/claude/crm-app-document-extraction-196mrk/backend/deploy/deploy-crm-corsi.sh && \
chmod +x /opt/crm-corsi/deploy-crm-corsi.sh && \
/opt/crm-corsi/deploy-crm-corsi.sh
```

Lo script si ferma due volte a chiedere: incolla il token Telegram, poi la
chiave Anthropic. Poi prosegue da solo (database, container, Nginx, HTTPS,
webhook Telegram, integrazione nel monitor) fino al messaggio
**"DEPLOY COMPLETATO!"**.

## 6. Verificare che funzioni

Apri Telegram, cerca `t.me/Aqr_Corsi_bot`, scrivi `/start` oppure il nome di
un'azienda. Se risponde, è tutto collegato correttamente.

## 7. Se qualcosa va storto

Nello stesso terminale VS Code (collegato alla VPS):
```bash
docker logs crm-corsi-app --tail 50
docker logs crm-corsi-db --tail 50
```
Copia l'output e condividilo in chat: da lì capisco cosa correggere.

## 8. Modificare il codice in futuro

1. Modifica i file in `backend/app/...` nella finestra VS Code **non**
   collegata alla VPS (quella con il codice locale)
2. Salva, poi dal pannello "Source Control" di VS Code: scrivi un messaggio
   di commit → **Commit** → **Sync/Push** (oppure chiedimi di farlo io e di
   pusharlo sullo stesso branch)
3. Torna nel terminale VS Code collegato alla VPS e rilancia lo stesso
   comando del punto 5: lo script fa `git pull` e ricostruisce il container
   automaticamente, senza toccare il `.env` con i segreti già configurati
