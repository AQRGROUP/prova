from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SessioneConversazione(Base):
    """Stato della conversazione WhatsApp in corso con un commerciale.

    Una sessione è identificata dal numero di telefono del commerciale e tiene
    traccia a quale azienda sta caricando lavoratori in questo momento.
    """

    __tablename__ = "sessioni_conversazione"

    id: Mapped[int] = mapped_column(primary_key=True)
    telefono: Mapped[str] = mapped_column(String(50), unique=True)
    stato: Mapped[str] = mapped_column(String(30), default="attesa_azienda")
    azienda_id: Mapped[int | None] = mapped_column(ForeignKey("aziende.id"), nullable=True)

    # JSON dell'anagrafica estratta da un documento lavoratore già ricevuto,
    # in attesa che arrivi il messaggio successivo con la mansione.
    lavoratore_dato_pendente: Mapped[str | None] = mapped_column(String, nullable=True)

    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
