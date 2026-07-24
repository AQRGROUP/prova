from app.models.azienda import Azienda
from app.models.lavoratore import Lavoratore
from app.models.corso import Corso, MansioneCorsoRule
from app.models.assegnazione import Assegnazione
from app.models.conversazione import SessioneConversazione

__all__ = [
    "Azienda",
    "Lavoratore",
    "Corso",
    "MansioneCorsoRule",
    "Assegnazione",
    "SessioneConversazione",
]
