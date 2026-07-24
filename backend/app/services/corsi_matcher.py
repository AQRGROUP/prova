"""Matching mansione -> corsi obbligatori, basato sulle regole seed."""

from dataclasses import dataclass

from app.services.mansione_classifier import classifica_mansione_ai
from seed.corsi_seed import CORSI, MANSIONE_RULES

_CORSI_BY_CHIAVE = {c["chiave"]: c for c in CORSI}


@dataclass
class CorsoAssegnato:
    chiave: str
    nome: str
    ore: int | None
    categoria: str


def _corso_da_chiave(chiave: str) -> CorsoAssegnato:
    dato = _CORSI_BY_CHIAVE[chiave]
    return CorsoAssegnato(chiave=chiave, nome=dato["nome"], ore=dato["ore"], categoria=dato["categoria"])


def corsi_per_mansione(mansione: str) -> list[CorsoAssegnato]:
    """Ritorna la lista (senza duplicati, in ordine di prima apparizione) dei
    corsi richiesti per una mansione, in base al match case-insensitive delle
    parole chiave nelle regole seed.
    """
    mansione_norm = mansione.strip().lower()
    chiavi_trovate: list[str] = []

    for regola in MANSIONE_RULES:
        if any(parola in mansione_norm for parola in regola["parole_chiave"]):
            for chiave in regola["corsi"]:
                if chiave not in chiavi_trovate:
                    chiavi_trovate.append(chiave)

    return [_corso_da_chiave(chiave) for chiave in chiavi_trovate]


def corsi_per_mansione_elastico(mansione: str) -> tuple[list[CorsoAssegnato], bool]:
    """Come `corsi_per_mansione`, ma quando nessuna regola nota fa match prova
    un fallback AI per non lasciare la mansione completamente scoperta.

    Ritorna (corsi, da_verificare). `da_verificare=True` significa che i corsi
    (se presenti) sono un suggerimento non basato su una regola validata e
    vanno controllati a mano prima di fidarsene: non deve mai essere trattato
    come un risultato definitivo tanto quanto un match diretto sulle regole.
    """
    corsi = corsi_per_mansione(mansione)
    if corsi:
        return corsi, False

    suggerimento = classifica_mansione_ai(mansione)
    if suggerimento is None:
        return [], True

    chiavi = ["gen_lav", f"spec_{suggerimento['rischio']}"]
    if suggerimento.get("richiede_haccp"):
        chiavi.append("haccp")

    return [_corso_da_chiave(chiave) for chiave in chiavi], True
