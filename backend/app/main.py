from fastapi import FastAPI, Request, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.conversation.handler import gestisci_messaggio
from app.database import Base, engine, get_db
from app.telegram.client import invia_documento, invia_messaggio_testo
from app.telegram.webhook import estrai_messaggi

app = FastAPI(title="CRM Corsi - Backend")

Base.metadata.create_all(bind=engine)


@app.post("/webhook/telegram")
async def ricevi_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Token webhook non valido")

    payload = await request.json()

    for chat_id, messaggio in estrai_messaggi(payload):
        risposta = gestisci_messaggio(db, chat_id, messaggio)

        for testo in risposta.messaggi:
            invia_messaggio_testo(chat_id, testo)

        if risposta.allegato:
            contenuto, filename, mime_type = risposta.allegato
            invia_documento(chat_id, contenuto, filename, mime_type)

    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
