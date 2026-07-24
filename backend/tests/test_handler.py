from app.conversation import states
from app.conversation.handler import MessaggioInbound, gestisci_messaggio
from app.models.azienda import Azienda
from app.models.conversazione import SessioneConversazione

TELEFONO = "393331112222"

DATI_DOCUMENTO_FAKE = {
    "nome": "Mario",
    "cognome": "Rossi",
    "data_nascita": "20/05/1990",
    "luogo_nascita": "Milano",
    "provincia_nascita": "MI",
    "sesso": "M",
    "codice_fiscale": "RSSMRA90E20F205X",
    "tipo_documento": "carta_identita",
}


def _patch_estrazione(monkeypatch, dati_documento=None, dati_visura=None):
    monkeypatch.setattr(
        "app.conversation.handler.scarica_media", lambda media_id: (b"contenuto-finto", "image/jpeg")
    )
    if dati_documento is not None:
        monkeypatch.setattr(
            "app.conversation.handler.estrai_documento_identita", lambda contenuto, mime: dati_documento
        )
    if dati_visura is not None:
        monkeypatch.setattr(
            "app.conversation.handler.estrai_visura_camerale", lambda contenuto, mime: dati_visura
        )


def test_nuova_azienda_da_testo_resta_in_attesa_visura(db_session):
    risposta = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))

    sessione = db_session.query(SessioneConversazione).filter_by(telefono=TELEFONO).one()
    assert sessione.stato == states.ATTESA_AZIENDA
    assert db_session.query(Azienda).filter_by(ragione_sociale="ACME SRL").one()
    assert "creata" in risposta.messaggi[0]


def test_continua_senza_visura_passa_a_lavoratori(db_session):
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))

    sessione = db_session.query(SessioneConversazione).filter_by(telefono=TELEFONO).one()
    assert sessione.stato == states.ATTESA_LAVORATORI


def test_azienda_esistente_trovata_per_nome(db_session):
    db_session.add(Azienda(ragione_sociale="BETA SPA", partita_iva="111"))
    db_session.commit()

    risposta = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="beta"))

    sessione = db_session.query(SessioneConversazione).filter_by(telefono=TELEFONO).one()
    assert sessione.stato == states.ATTESA_LAVORATORI
    assert "esistente" in risposta.messaggi[0]


def test_mansione_non_riconosciuta_segnala_da_verificare(db_session, monkeypatch):
    _patch_estrazione(monkeypatch, dati_documento=DATI_DOCUMENTO_FAKE)
    monkeypatch.setattr("app.services.corsi_matcher.classifica_mansione_ai", lambda mansione: None)
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))

    risposta = gestisci_messaggio(
        db_session, TELEFONO, MessaggioInbound(tipo="immagine", media_id="m1", caption="Astronauta")
    )

    assert "verificata e assegnata a mano" in risposta.messaggi[0]


def test_documento_con_caption_crea_lavoratore_subito(db_session, monkeypatch):
    _patch_estrazione(monkeypatch, dati_documento=DATI_DOCUMENTO_FAKE)
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))

    risposta = gestisci_messaggio(
        db_session, TELEFONO, MessaggioInbound(tipo="immagine", media_id="m1", caption="Operaio edile")
    )

    assert "Mario Rossi" in risposta.messaggi[0]
    assert "Formazione Generale Lavoratori" in risposta.messaggi[0]


def test_documento_senza_caption_poi_mansione_in_messaggio_successivo(db_session, monkeypatch):
    _patch_estrazione(monkeypatch, dati_documento=DATI_DOCUMENTO_FAKE)
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))

    risposta_1 = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="immagine", media_id="m1"))
    assert "mansione" in risposta_1.messaggi[0].lower()

    risposta_2 = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="Cuoco"))
    assert "Mario Rossi" in risposta_2.messaggi[0]
    assert "HACCP" in risposta_2.messaggi[0]


def test_riepilogo_e_esporta(db_session, monkeypatch):
    _patch_estrazione(monkeypatch, dati_documento=DATI_DOCUMENTO_FAKE)
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="immagine", media_id="m1", caption="Cuoco"))

    riepilogo = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="fine"))
    assert "Mario Rossi" in riepilogo.messaggi[0]
    assert "1 lavoratori" in riepilogo.messaggi[0]

    export = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="esporta"))
    assert export.allegato is not None
    contenuto, filename, mime = export.allegato
    assert filename.endswith(".csv")
    assert b"Mario" in contenuto


def test_nuova_azienda_reset_sessione(db_session):
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="ACME SRL"))
    gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="continua"))

    risposta = gestisci_messaggio(db_session, TELEFONO, MessaggioInbound(tipo="testo", testo="nuova azienda"))

    sessione = db_session.query(SessioneConversazione).filter_by(telefono=TELEFONO).one()
    assert sessione.stato == states.ATTESA_AZIENDA
    assert sessione.azienda_id is None
    assert "nuova azienda" in risposta.messaggi[0].lower()
