"""Parsing degli update della Telegram Bot API verso MessaggioInbound."""

from app.conversation.handler import MessaggioInbound


def estrai_messaggi(payload: dict) -> list[tuple[str, MessaggioInbound]]:
    """Ritorna una lista di (chat_id, messaggio) da un update Telegram.

    Un update Telegram contiene sempre un solo messaggio (a differenza del
    payload WhatsApp che può raggrupparne più d'uno): la lista è per
    coerenza con il resto del codice, non perché ce ne aspettiamo più di uno.
    """
    messaggio = payload.get("message")
    if messaggio is None:
        return []

    chat_id = str(messaggio["chat"]["id"])

    if "photo" in messaggio:
        # Telegram manda più risoluzioni della stessa foto: l'ultima è la più grande.
        file_id = messaggio["photo"][-1]["file_id"]
        inbound = MessaggioInbound(tipo="immagine", media_id=file_id, caption=messaggio.get("caption"))
    elif "document" in messaggio:
        file_id = messaggio["document"]["file_id"]
        inbound = MessaggioInbound(tipo="documento", media_id=file_id, caption=messaggio.get("caption"))
    elif "text" in messaggio:
        inbound = MessaggioInbound(tipo="testo", testo=messaggio["text"])
    else:
        return []

    return [(chat_id, inbound)]
