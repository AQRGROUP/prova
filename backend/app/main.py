from fastapi import FastAPI, Request, Response, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.conversation.handler import gestisci_messaggio
from app.database import Base, engine, get_db
from app.whatsapp.client import invia_documento, invia_messaggio_testo
from app.whatsapp.webhook import estrai_messaggi

app = FastAPI(title="CRM Corsi - Backend")

Base.metadata.create_all(bind=engine)


@app.get("/webhook/whatsapp")
def verifica_webhook(request: Request):
    """Verifica iniziale richiesta da Meta quando si configura il webhook."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@app.post("/webhook/whatsapp")
async def ricevi_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    for telefono, messaggio in estrai_messaggi(payload):
        risposta = gestisci_messaggio(db, telefono, messaggio)

        for testo in risposta.messaggi:
            invia_messaggio_testo(telefono, testo)

        if risposta.allegato:
            contenuto, filename, mime_type = risposta.allegato
            invia_documento(telefono, contenuto, filename, mime_type)

    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
