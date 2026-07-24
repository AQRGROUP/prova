# Come mettere online il bot CRM Corsi (VPS Hostinger)

Segue lo stesso schema usato per le altre app sulla VPS (es. PortaleCSE):
un container Docker per l'app, uno per il database Postgres, Nginx davanti
con HTTPS via Certbot.

## Prima di iniziare

Assicurati di avere a portata di mano:
- Il **token del bot Telegram** (da @BotFather) — `8886730854:AAHRga9...`
- Una **chiave Anthropic dedicata** a questo bot: creala su
  console.anthropic.com → Settings → API Keys → Create Key
- Il DNS di `corsibot.safetyprosuite.com` puntato all'IP della VPS
  (`72.61.189.136`), tipo A record. Se il dominio principale è già gestito
  lì, basta aggiungere questo sottodominio nel pannello DNS.

## Passaggi

1. Connettiti alla VPS via SSH (dallo stesso terminale/PowerShell che usi
   per gli altri script):
   ```
   ssh root@72.61.189.136
   ```
2. Scarica lo script di deploy (basta farlo una volta, poi resta sulla VPS):
   ```bash
   mkdir -p /opt/crm-corsi
   curl -o /opt/crm-corsi/deploy-crm-corsi.sh \
     https://raw.githubusercontent.com/aqrgroup/prova/claude/crm-app-document-extraction-196mrk/backend/deploy/deploy-crm-corsi.sh
   chmod +x /opt/crm-corsi/deploy-crm-corsi.sh
   ```
3. Eseguilo:
   ```bash
   /opt/crm-corsi/deploy-crm-corsi.sh
   ```
4. Quando te lo chiede, incolla il **token Telegram** e la **chiave
   Anthropic** (restano solo nel `.env` sulla VPS, non finiscono mai su git).
5. Aspetta il messaggio finale "DEPLOY COMPLETATO!"

## Come verificare che funzioni

Apri Telegram, cerca il bot su **t.me/Aqr_Corsi_bot**, scrivi `/start` o il
nome di un'azienda. Se risponde, è tutto collegato correttamente.

## Se qualcosa non va

```bash
docker logs crm-corsi-app --tail 50
docker logs crm-corsi-db --tail 50
```

Il container va in ascolto sulla porta **8022** (app) e **5440** (database),
scelte per non entrare in conflitto con le altre app già sulla VPS — lo
script verifica comunque che siano libere prima di procedere e si ferma con
un errore chiaro se non lo sono.

## Aggiornare dopo modifiche al codice

Rilancia semplicemente lo stesso script:
```bash
/opt/crm-corsi/deploy-crm-corsi.sh
```
Aggiorna il codice (git pull) e ricostruisce il container. Il `.env` con i
segreti non viene mai toccato una volta creato.
