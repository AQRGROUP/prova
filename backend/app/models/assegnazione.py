from datetime import date, datetime, timezone

from sqlalchemy import String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Assegnazione(Base):
    """Un corso assegnato a un lavoratore, con lo stato di avanzamento."""

    __tablename__ = "assegnazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    lavoratore_id: Mapped[int] = mapped_column(ForeignKey("lavoratori.id"))
    corso_id: Mapped[int] = mapped_column(ForeignKey("corsi.id"))

    stato: Mapped[str] = mapped_column(String(20), default="da_fare")  # da_fare | in_corso | completato
    data_completamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    attestato_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    creato_il: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    lavoratore: Mapped["Lavoratore"] = relationship(back_populates="assegnazioni")
    corso: Mapped["Corso"] = relationship()
