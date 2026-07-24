"""Client minimale per la Telegram Bot API.

Molto più semplice della WhatsApp Cloud API: basta un token da @BotFather,
nessuna verifica aziendale, nessun webhook di verifica separato. Le chiamate
reali non sono testate in questo repo (nessun token disponibile in questo
ambiente): vanno verificate una volta creato un bot vero.
"""

import mimetypes

import httpx

from app.config import settings

_API_BASE_URL = "https://api.telegram.org/bot{token}"
_FILE_BASE_URL = "https://api.telegram.org/file/bot{token}"


def _api_url(metodo: str) -> str:
    return f"{_API_BASE_URL.format(token=settings.telegram_bot_token)}/{metodo}"


def invia_messaggio_testo(chat_id: str, testo: str) -> None:
    response = httpx.post(_api_url("sendMessage"), json={"chat_id": chat_id, "text": testo}, timeout=30)
    response.raise_for_status()


def scarica_media(file_id: str) -> tuple[bytes, str]:
    """Ritorna (contenuto, mime_type) di un file (foto/documento) ricevuto via webhook."""
    info = httpx.get(_api_url("getFile"), params={"file_id": file_id}, timeout=30)
    info.raise_for_status()
    file_path = info.json()["result"]["file_path"]

    file_url = f"{_FILE_BASE_URL.format(token=settings.telegram_bot_token)}/{file_path}"
    content = httpx.get(file_url, timeout=30)
    content.raise_for_status()

    mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
    return content.content, mime_type


def invia_documento(chat_id: str, contenuto: bytes, filename: str, mime_type: str) -> None:
    files = {"document": (filename, contenuto, mime_type)}
    response = httpx.post(_api_url("sendDocument"), data={"chat_id": chat_id}, files=files, timeout=60)
    response.raise_for_status()


def imposta_webhook(url_pubblico: str) -> None:
    """Registra l'URL del webhook presso Telegram. Da chiamare una volta sola
    (o quando cambia l'URL pubblico del backend), non ad ogni avvio."""
    params = {"url": url_pubblico}
    if settings.telegram_webhook_secret:
        params["secret_token"] = settings.telegram_webhook_secret
    response = httpx.post(_api_url("setWebhook"), params=params, timeout=30)
    response.raise_for_status()
