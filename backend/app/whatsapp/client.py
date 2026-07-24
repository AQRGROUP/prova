"""Client minimale per la WhatsApp Cloud API (Meta).

Richiede WHATSAPP_ACCESS_TOKEN e WHATSAPP_PHONE_NUMBER_ID configurati. Le
chiamate reali non sono testate in questo repo (nessuna credenziale
disponibile in questo ambiente): vanno verificate una volta collegato un
numero WhatsApp Business reale.
"""

import httpx

from app.config import settings

_GRAPH_BASE_URL = "https://graph.facebook.com/v20.0"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.whatsapp_access_token}"}


def invia_messaggio_testo(telefono: str, testo: str) -> None:
    url = f"{_GRAPH_BASE_URL}/{settings.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": testo},
    }
    response = httpx.post(url, headers=_headers(), json=payload, timeout=30)
    response.raise_for_status()


def scarica_media(media_id: str) -> tuple[bytes, str]:
    """Ritorna (contenuto, mime_type) di un media ricevuto via webhook."""
    info_url = f"{_GRAPH_BASE_URL}/{media_id}"
    info = httpx.get(info_url, headers=_headers(), timeout=30)
    info.raise_for_status()
    media_url = info.json()["url"]
    mime_type = info.json().get("mime_type", "image/jpeg")

    content = httpx.get(media_url, headers=_headers(), timeout=30)
    content.raise_for_status()
    return content.content, mime_type


def invia_documento(telefono: str, contenuto: bytes, filename: str, mime_type: str) -> None:
    upload_url = f"{_GRAPH_BASE_URL}/{settings.whatsapp_phone_number_id}/media"
    files = {"file": (filename, contenuto, mime_type)}
    data = {"messaging_product": "whatsapp"}
    upload = httpx.post(upload_url, headers=_headers(), data=data, files=files, timeout=60)
    upload.raise_for_status()
    media_id = upload.json()["id"]

    send_url = f"{_GRAPH_BASE_URL}/{settings.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "document",
        "document": {"id": media_id, "filename": filename},
    }
    response = httpx.post(send_url, headers=_headers(), json=payload, timeout=30)
    response.raise_for_status()
