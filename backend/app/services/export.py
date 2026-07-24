"""Generazione file di export nei tracciati usati dal cliente.

- CSV "Importazione": stesso formato del template fornito, una riga per ogni
  combinazione lavoratore+corso (è così che la piattaforma corsi si aspetta i
  dati per l'iscrizione bulk).
- XLSX "Allegato 1": riepilogo lavoratore/mansione/azienda/ATECO/datore di
  lavoro. Il "Registro" (presenze per data corso) richiede le date delle
  sessioni del corso, non ancora note in questa fase di raccolta dati, quindi
  non è generato qui.
"""

import csv
import io

from openpyxl import Workbook

from app.models.azienda import Azienda
from app.models.lavoratore import Lavoratore
from app.services.corsi_matcher import corsi_per_mansione_elastico

IMPORTAZIONE_HEADER = [
    "NOME*",
    "COGNOME*",
    "EMAIL*",
    "DATA DI NASCITA (GG/MM/AAAA)*",
    "LUOGO DI NASCITA*",
    "AREA (come indicato su piattaforma)",
    "CODICE FISCALE*",
    "TELEFONO",
    "QUALIFICA*",
    "AZIENDA (inserire partita iva)",
    "CORSO (SKU corso)",
]


def _corso_label(corso, da_verificare: bool) -> str:
    """SKU se disponibile, altrimenti il nome del corso con prefissi che
    segnalano: SKU reale ancora da assegnare, e se il corso stesso è un
    suggerimento non basato su una regola validata (mansione sconosciuta)."""
    prefisso_verifica = "DA_VERIFICARE:" if da_verificare else ""
    return f"{prefisso_verifica}MANCA_SKU:{corso.nome}"


def genera_csv_importazione(azienda: Azienda, lavoratori: list[Lavoratore]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORTAZIONE_HEADER)

    for lavoratore in lavoratori:
        corsi, da_verificare = corsi_per_mansione_elastico(lavoratore.mansione)
        # Se nessuna regola/AI ha prodotto un corso, esporta comunque una riga
        # senza corso così il lavoratore non si perde e va assegnato a mano.
        righe_corsi = corsi or [None]

        for corso in righe_corsi:
            writer.writerow(
                [
                    lavoratore.nome,
                    lavoratore.cognome,
                    lavoratore.email or "",
                    lavoratore.data_nascita.strftime("%d/%m/%Y") if lavoratore.data_nascita else "",
                    lavoratore.luogo_nascita or "",
                    lavoratore.area or "",
                    lavoratore.codice_fiscale or "",
                    lavoratore.telefono or "",
                    lavoratore.mansione,
                    azienda.partita_iva or "",
                    _corso_label(corso, da_verificare) if corso else "",
                ]
            )

    return buffer.getvalue()


def genera_xlsx_allegato1(azienda: Azienda, lavoratori: list[Lavoratore], datore_di_lavoro: str = "") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Allegato 1"
    ws.append(["LAVORATORI", "MANSIONE", "AZIENDA", "ATECO", "DATORE DI LAVORO"])

    for lavoratore in lavoratori:
        ws.append(
            [
                f"{lavoratore.cognome} {lavoratore.nome}",
                lavoratore.mansione,
                azienda.ragione_sociale,
                azienda.ateco or "",
                datore_di_lavoro,
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
