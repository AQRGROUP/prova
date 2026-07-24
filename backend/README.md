# CRM Corsi - Backend

Backend per il commerciale: raccolta dati aziende/lavoratori via Telegram,
estrazione anagrafica da foto documenti, matching mansione -> corsi
obbligatori, export nel tracciato "Importazione" usato dalla piattaforma
corsi esistente.

## Flusso

1. Il commerciale scrive al bot Telegram il nome dell'azienda oppure allega
   la visura camerale (i dati vengono estratti automaticamente).
2. Per ogni lavoratore: foto del documento d'identità, con la mansione in
   didascalia oppure nel messaggio successivo.
3. Comandi disponibili in questa fase: `fine` / `riepilogo` (mostra i
   lavoratori raccolti e i corsi associati), `esporta` (genera il CSV nel
   formato "Importazione"), `nuova azienda` (ricomincia con un'altra azienda).

## Setup

```bash
pip install -e .
```

Variabili d'ambiente richieste (`.env` o env reali), vedi `app/config.py`:

- `DATABASE_URL` (default sqlite locale, da sostituire con Postgres in produzione)
- `TELEGRAM_BOT_TOKEN` (ottenuto da @BotFather su Telegram)
- `TELEGRAM_WEBHOOK_SECRET` (opzionale ma consigliato, per verificare che le richieste al webhook arrivino davvero da Telegram)
- `ANTHROPIC_API_KEY` (per l'estrazione documenti via Claude vision)
- `DEFAULT_EMAIL_FALLBACK_DOMAIN` (opzionale, non ancora usato: l'email di fallback attuale è quella registrata sull'azienda)

Creazione del bot: si scrive a **@BotFather** su Telegram, si sceglie un
nome, e si ottiene subito il token da mettere in `TELEGRAM_BOT_TOKEN`.
Nessuna verifica aziendale richiesta.

Una volta che il backend è online su un URL pubblico HTTPS, si registra il
webhook chiamando una sola volta `app.telegram.client.imposta_webhook(url)`
con l'URL pubblico (es. `https://tuo-dominio.it/webhook/telegram`).

Avvio locale:

```bash
uvicorn app.main:app --reload
```

Test (logica pura, nessuna credenziale esterna richiesta):

```bash
python -m pytest
```

## Cosa manca prima di andare in produzione

- **Credenziali reali**: nessuna chiamata a Telegram/Anthropic è testata in
  questo ambiente (nessuna credenziale disponibile). Vanno verificate con un
  bot Telegram reale e una chiave Anthropic valida.
- **Tabella corsi**: `seed/corsi_seed.py` è un punto di partenza basato sullo
  schema generale del Nuovo Accordo Stato-Regioni + HACCP alimentaristi, da
  validare e correggere con dati reali (in particolare gli SKU corso, oggi
  vuoti/placeholder `MANCA_SKU:`).
- **Migrazioni DB**: le tabelle vengono create con `create_all` per comodità
  di sviluppo; per produzione conviene introdurre Alembic (dipendenza già
  presente in `pyproject.toml`, migrazioni da scrivere).
- **Hosting + dominio pubblico HTTPS** per il webhook Telegram.
- **Osservazione dai dati di esempio forniti**: nel template reale il campo
  EMAIL è spesso lasciato come testo letterale "EMAIL*" (nessuna email reale
  disponibile); qui è stato implementato l'uso dell'email aziendale come
  fallback per ogni lavoratore, come deciso in fase di analisi - da
  confermare che sia compatibile con l'import sulla piattaforma.
- **Registro presenze**: l'export "Registro" (con le date delle sessioni
  corso) non è generato: richiede le date effettive delle sessioni, non
  disponibili in fase di raccolta dati. Generato solo l'"Allegato 1"
  (lavoratore/mansione/azienda/ATECO/datore di lavoro).
