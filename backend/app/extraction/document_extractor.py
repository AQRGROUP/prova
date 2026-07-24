"""Estrazione dati strutturati da foto di documenti, usando Claude in modalità
visione. Evita di dover integrare OCR + parsing separati: si manda la foto e
si chiede direttamente un JSON con i campi che servono.
"""

import json
import re

from anthropic import Anthropic

from app.config import settings

_DOCUMENTO_IDENTITA_PROMPT = """Guarda la foto di questo documento d'identità italiano (carta d'identità, patente o passaporto) ed estrai i seguenti campi in JSON. Se un campo non è leggibile o non presente, usa null. Rispondi SOLO con il JSON, nessun altro testo.

{
  "nome": string,
  "cognome": string,
  "data_nascita": string in formato GG/MM/AAAA,
  "luogo_nascita": string (comune),
  "provincia_nascita": string (sigla provincia, o null se estero),
  "sesso": "M" o "F",
  "codice_fiscale": string o null se non presente sul documento,
  "tipo_documento": "carta_identita" | "patente" | "passaporto"
}
"""

_VISURA_CAMERALE_PROMPT = """Guarda questa visura camerale italiana ed estrai i seguenti campi in JSON. Se un campo non è leggibile o non presente, usa null. Rispondi SOLO con il JSON, nessun altro testo.

{
  "ragione_sociale": string,
  "partita_iva": string,
  "ateco": string (codice ATECO principale),
  "indirizzo": string (sede legale),
  "comune": string,
  "provincia": string (sigla),
  "regione": string
}
"""


def _client() -> Anthropic:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY non configurata: impostala nelle variabili d'ambiente "
            "per abilitare l'estrazione documenti."
        )
    return Anthropic(api_key=settings.anthropic_api_key)


def _estrai_json_da_risposta(testo: str) -> dict:
    testo = testo.strip()
    # Rimuove eventuali code fence markdown se il modello le include comunque.
    match = re.search(r"\{.*\}", testo, re.DOTALL)
    if not match:
        raise ValueError(f"Nessun JSON trovato nella risposta del modello: {testo!r}")
    return json.loads(match.group(0))


def _chiama_claude_vision(prompt: str, image_bytes: bytes, media_type: str) -> dict:
    import base64

    client = _client()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    testo = "".join(block.text for block in response.content if block.type == "text")
    return _estrai_json_da_risposta(testo)


def estrai_documento_identita(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    return _chiama_claude_vision(_DOCUMENTO_IDENTITA_PROMPT, image_bytes, media_type)


def estrai_visura_camerale(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    return _chiama_claude_vision(_VISURA_CAMERALE_PROMPT, image_bytes, media_type)
