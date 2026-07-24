"""Parsing dei payload del webhook WhatsApp Cloud API verso MessaggioInbound."""

from app.conversation.handler import MessaggioInbound


def estrai_messaggi(payload: dict) -> list[tuple[str, MessaggioInbound]]:
    """Ritorna una lista di (telefono, messaggio) da un payload di webhook.

    Un payload può contenere più entry/change/messaggi in teoria; nella
    pratica WhatsApp ne manda quasi sempre uno solo, ma iteriamo per sicurezza.
    """
    risultati: list[tuple[str, MessaggioInbound]] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            valore = change.get("value", {})
            for messaggio in valore.get("messages", []):
                telefono = messaggio.get("from")
                tipo = messaggio.get("type")

                if tipo == "text":
                    inbound = MessaggioInbound(tipo="testo", testo=messaggio.get("text", {}).get("body"))
                elif tipo == "image":
                    img = messaggio.get("image", {})
                    inbound = MessaggioInbound(tipo="immagine", media_id=img.get("id"), caption=img.get("caption"))
                elif tipo == "document":
                    doc = messaggio.get("document", {})
                    inbound = MessaggioInbound(tipo="documento", media_id=doc.get("id"), caption=doc.get("caption"))
                else:
                    continue

                if telefono:
                    risultati.append((telefono, inbound))

    return risultati
