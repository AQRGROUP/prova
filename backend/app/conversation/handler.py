"""State machine della conversazione Telegram con il commerciale.

Flusso:
  ATTESA_AZIENDA -> il commerciale scrive il nome azienda (cerca/crea) oppure
                     allega la visura camerale (estrae i dati automaticamente)
  ATTESA_LAVORATORI -> il commerciale manda foto documento (+ mansione in
                        didascalia, o mansione nel messaggio successivo) per
                        ogni lavoratore. Comandi: "fine"/"riepilogo", "esporta",
                        "nuova azienda".
"""

import json
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.conversation import states
from app.conversation.states import ATTESA_AZIENDA, ATTESA_LAVORATORI
from app.extraction.document_extractor import estrai_documento_identita, estrai_visura_camerale
from app.models.azienda import Azienda
from app.models.conversazione import SessioneConversazione
from app.models.lavoratore import Lavoratore
from app.services.corsi_matcher import corsi_per_mansione_elastico
from app.services.export import genera_csv_importazione, genera_xlsx_allegato1
from app.telegram.client import scarica_media

COMANDI_NUOVA_AZIENDA = {"nuova azienda", "cambia azienda"}
COMANDI_RIEPILOGO = {"fine", "riepilogo"}
COMANDI_ESPORTA = {"esporta", "esporta csv"}


@dataclass
class MessaggioInbound:
    tipo: str  # "testo" | "immagine" | "documento"
    testo: str | None = None
    caption: str | None = None
    media_id: str | None = None


@dataclass
class RispostaConversazione:
    messaggi: list[str]
    allegato: tuple[bytes, str, str] | None = None  # (contenuto, filename, mime_type)


_FORMATI_DATA = ("%d/%m/%Y", "%d-%m-%Y")


def _parse_data_italiana(testo: str | None) -> date | None:
    if not testo:
        return None
    testo = testo.strip()
    for formato in _FORMATI_DATA:
        try:
            return datetime.strptime(testo, formato).date()
        except ValueError:
            continue
    return None


def _get_or_create_sessione(db: Session, chat_id: str) -> SessioneConversazione:
    sessione = db.query(SessioneConversazione).filter_by(chat_id=chat_id).first()
    if sessione is None:
        sessione = SessioneConversazione(chat_id=chat_id, stato=ATTESA_AZIENDA)
        db.add(sessione)
        db.flush()
    return sessione


def _reset_a_nuova_azienda(sessione: SessioneConversazione) -> RispostaConversazione:
    sessione.stato = ATTESA_AZIENDA
    sessione.azienda_id = None
    sessione.lavoratore_dato_pendente = None
    return RispostaConversazione(
        ["Ok, ripartiamo da una nuova azienda. Scrivi il nome/P.IVA oppure allega la visura camerale."]
    )


def _crea_lavoratore(db: Session, azienda: Azienda, dati: dict, mansione: str) -> Lavoratore:
    lavoratore = Lavoratore(
        azienda_id=azienda.id,
        nome=dati.get("nome") or "",
        cognome=dati.get("cognome") or "",
        email=azienda.email_aziendale,
        email_e_fallback_aziendale=bool(azienda.email_aziendale),
        data_nascita=_parse_data_italiana(dati.get("data_nascita")),
        luogo_nascita=dati.get("luogo_nascita"),
        provincia_nascita=dati.get("provincia_nascita"),
        sesso=dati.get("sesso"),
        codice_fiscale=dati.get("codice_fiscale"),
        mansione=mansione.strip(),
        area=azienda.regione,
        documento_tipo=dati.get("tipo_documento"),
        documento_raw_extraction=json.dumps(dati, ensure_ascii=False),
    )
    db.add(lavoratore)
    db.flush()
    return lavoratore


def _messaggio_conferma_lavoratore(lavoratore: Lavoratore) -> str:
    intestazione = f"Registrato {lavoratore.nome} {lavoratore.cognome} ({lavoratore.mansione})."
    corsi, da_verificare = corsi_per_mansione_elastico(lavoratore.mansione)

    if corsi and not da_verificare:
        elenco = ", ".join(c.nome for c in corsi)
        return f"{intestazione} Corsi richiesti: {elenco}."
    if corsi and da_verificare:
        elenco = ", ".join(c.nome for c in corsi)
        return (
            f"{intestazione} Mansione non tra le regole note: corsi SUGGERITI (da verificare a mano): {elenco}."
        )
    return f"{intestazione} Nessun corso trovato per questa mansione: va verificata e assegnata a mano."


def _gestisci_attesa_azienda(db: Session, sessione: SessioneConversazione, messaggio: MessaggioInbound) -> RispostaConversazione:
    if messaggio.tipo in ("immagine", "documento"):
        contenuto, mime = scarica_media(messaggio.media_id)
        dati = estrai_visura_camerale(contenuto, mime)

        azienda = None
        if dati.get("partita_iva"):
            azienda = db.query(Azienda).filter_by(partita_iva=dati["partita_iva"]).first()
        if azienda is None:
            azienda = Azienda(ragione_sociale=dati.get("ragione_sociale") or "Azienda senza nome")
            db.add(azienda)

        azienda.ragione_sociale = dati.get("ragione_sociale") or azienda.ragione_sociale
        azienda.partita_iva = dati.get("partita_iva") or azienda.partita_iva
        azienda.ateco = dati.get("ateco") or azienda.ateco
        azienda.indirizzo = dati.get("indirizzo") or azienda.indirizzo
        azienda.comune = dati.get("comune") or azienda.comune
        azienda.provincia = dati.get("provincia") or azienda.provincia
        azienda.regione = dati.get("regione") or azienda.regione
        azienda.visura_raw_extraction = json.dumps(dati, ensure_ascii=False)
        db.flush()

        sessione.azienda_id = azienda.id
        sessione.stato = ATTESA_LAVORATORI
        return RispostaConversazione(
            [
                f"Azienda '{azienda.ragione_sociale}' registrata (P.IVA {azienda.partita_iva or 'n.d.'}). "
                "Ora mandami foto documento + mansione per ogni lavoratore."
            ]
        )

    testo = (messaggio.testo or "").strip()

    if testo.lower() == "continua" and sessione.azienda_id:
        sessione.stato = ATTESA_LAVORATORI
        return RispostaConversazione(["Ok, procediamo senza visura. Mandami foto documento + mansione per ogni lavoratore."])

    azienda_esistente = db.query(Azienda).filter(Azienda.ragione_sociale.ilike(f"%{testo}%")).first()
    if azienda_esistente:
        sessione.azienda_id = azienda_esistente.id
        sessione.stato = ATTESA_LAVORATORI
        return RispostaConversazione(
            [f"Trovata azienda esistente: {azienda_esistente.ragione_sociale}. Ora mandami foto documento + mansione per ogni lavoratore."]
        )

    nuova_azienda = Azienda(ragione_sociale=testo)
    db.add(nuova_azienda)
    db.flush()
    sessione.azienda_id = nuova_azienda.id
    return RispostaConversazione(
        [f"Nuova azienda '{testo}' creata. Allega la visura camerale per completare P.IVA/ATECO/sede, oppure scrivi 'continua' per procedere senza."]
    )


def _riepilogo(db: Session, azienda: Azienda) -> str:
    lavoratori = db.query(Lavoratore).filter_by(azienda_id=azienda.id).all()
    if not lavoratori:
        return f"Nessun lavoratore ancora registrato per {azienda.ragione_sociale}."

    righe = [f"Riepilogo {azienda.ragione_sociale} ({len(lavoratori)} lavoratori):"]
    for lavoratore in lavoratori:
        corsi, da_verificare = corsi_per_mansione_elastico(lavoratore.mansione)
        nomi_corsi = ", ".join(c.nome for c in corsi) or "nessun corso trovato"
        marcatore = " [DA VERIFICARE]" if da_verificare else ""
        righe.append(f"- {lavoratore.nome} {lavoratore.cognome} | {lavoratore.mansione} | {nomi_corsi}{marcatore}")
    righe.append("Scrivi 'esporta' per generare il file da caricare in piattaforma.")
    return "\n".join(righe)


def _gestisci_attesa_lavoratori(db: Session, sessione: SessioneConversazione, messaggio: MessaggioInbound) -> RispostaConversazione:
    azienda = db.get(Azienda, sessione.azienda_id)

    if messaggio.tipo == "testo":
        testo_norm = (messaggio.testo or "").strip().lower()

        if sessione.lavoratore_dato_pendente:
            dati = json.loads(sessione.lavoratore_dato_pendente)
            lavoratore = _crea_lavoratore(db, azienda, dati, messaggio.testo or "")
            sessione.lavoratore_dato_pendente = None
            return RispostaConversazione([_messaggio_conferma_lavoratore(lavoratore)])

        if testo_norm in COMANDI_RIEPILOGO:
            return RispostaConversazione([_riepilogo(db, azienda)])

        if testo_norm in COMANDI_ESPORTA:
            lavoratori = db.query(Lavoratore).filter_by(azienda_id=azienda.id).all()
            csv_content = genera_csv_importazione(azienda, lavoratori)
            filename = f"importazione_{azienda.ragione_sociale.replace(' ', '_')}.csv"
            return RispostaConversazione(
                [f"Export pronto per {azienda.ragione_sociale} ({len(lavoratori)} lavoratori)."],
                allegato=(csv_content.encode("utf-8"), filename, "text/csv"),
            )

        return RispostaConversazione(
            ["Manda la foto del documento del lavoratore (con la mansione in didascalia), oppure scrivi 'fine' per il riepilogo o 'esporta' per il file."]
        )

    # immagine o documento: estrazione anagrafica lavoratore
    contenuto, mime = scarica_media(messaggio.media_id)
    dati = estrai_documento_identita(contenuto, mime)

    if messaggio.caption:
        lavoratore = _crea_lavoratore(db, azienda, dati, messaggio.caption)
        return RispostaConversazione([_messaggio_conferma_lavoratore(lavoratore)])

    sessione.lavoratore_dato_pendente = json.dumps(dati, ensure_ascii=False)
    nome = dati.get("nome") or ""
    cognome = dati.get("cognome") or ""
    return RispostaConversazione([f"Documento ricevuto per {nome} {cognome}. Qual è la sua mansione?"])


def gestisci_messaggio(db: Session, chat_id: str, messaggio: MessaggioInbound) -> RispostaConversazione:
    sessione = _get_or_create_sessione(db, chat_id)

    if messaggio.tipo == "testo" and (messaggio.testo or "").strip().lower() in COMANDI_NUOVA_AZIENDA:
        risposta = _reset_a_nuova_azienda(sessione)
        db.commit()
        return risposta

    if sessione.stato == states.ATTESA_AZIENDA:
        risposta = _gestisci_attesa_azienda(db, sessione, messaggio)
    else:
        risposta = _gestisci_attesa_lavoratori(db, sessione, messaggio)

    db.commit()
    return risposta
