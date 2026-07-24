"""Fallback AI per mansioni non coperte dalle regole seed (keyword-based).

Usato solo quando `corsi_matcher.corsi_per_mansione` non trova nessuna regola:
prova a classificare rischio/HACCP via Claude così una mansione mai vista
(sinonimo, mansione in un'altra lingua, refuso) ottiene comunque un
suggerimento, che però resta sempre marcato come "da verificare" a valle
(vedi `corsi_per_mansione_elastico`) perché non è una regola validata.
"""

import json
import re

from anthropic import Anthropic

from app.config import settings

_PROMPT = """Sei un esperto di sicurezza sul lavoro (D.Lgs 81/08 e Nuovo Accordo Stato-Regioni). \
Data questa mansione lavorativa: "{mansione}", classifica in JSON:

{{"rischio": "basso" | "medio" | "alto", "richiede_haccp": true | false}}

"rischio" è il livello di rischio ai fini della Formazione Specifica Lavoratori. \
"richiede_haccp" è true se la mansione comporta manipolazione/somministrazione di alimenti. \
Rispondi SOLO con il JSON, nessun altro testo."""


def classifica_mansione_ai(mansione: str) -> dict | None:
    """Ritorna {"rischio": ..., "richiede_haccp": ...} oppure None se
    l'estrazione non è disponibile (nessuna API key) o fallisce."""
    if not settings.anthropic_api_key:
        return None

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=200,
            messages=[{"role": "user", "content": _PROMPT.format(mansione=mansione)}],
        )
        testo = "".join(block.text for block in response.content if block.type == "text")
        match = re.search(r"\{.*\}", testo, re.DOTALL)
        if not match:
            return None
        dati = json.loads(match.group(0))
        if dati.get("rischio") not in ("basso", "medio", "alto"):
            return None
        return dati
    except Exception:
        # Un fallback che può fallire in mille modi diversi (rete, quota,
        # risposta malformata) non deve mai bloccare la conversazione:
        # il chiamante tratta None come "nessun suggerimento disponibile".
        return None
