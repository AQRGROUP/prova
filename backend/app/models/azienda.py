from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Azienda(Base):
    __tablename__ = "aziende"

    id: Mapped[int] = mapped_column(primary_key=True)
    ragione_sociale: Mapped[str] = mapped_column(String(255))
    partita_iva: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    ateco: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_aziendale: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    indirizzo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comune: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(10), nullable=True)
    regione: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # JSON grezzo restituito dall'estrazione della visura camerale, tenuto per
    # audit/debug quando i campi strutturati non bastano.
    visura_raw_extraction: Mapped[str | None] = mapped_column(String, nullable=True)

    creato_il: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    lavoratori: Mapped[list["Lavoratore"]] = relationship(back_populates="azienda")
