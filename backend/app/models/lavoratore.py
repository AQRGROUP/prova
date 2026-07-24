from datetime import date, datetime, timezone

from sqlalchemy import String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Lavoratore(Base):
    __tablename__ = "lavoratori"

    id: Mapped[int] = mapped_column(primary_key=True)
    azienda_id: Mapped[int] = mapped_column(ForeignKey("aziende.id"))

    nome: Mapped[str] = mapped_column(String(100))
    cognome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # true quando l'email è quella aziendale di fallback e non quella personale
    email_e_fallback_aziendale: Mapped[bool] = mapped_column(default=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)

    data_nascita: Mapped[date | None] = mapped_column(Date, nullable=True)
    luogo_nascita: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia_nascita: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sesso: Mapped[str | None] = mapped_column(String(1), nullable=True)
    codice_fiscale: Mapped[str | None] = mapped_column(String(16), nullable=True)

    mansione: Mapped[str] = mapped_column(String(255))
    # Regione/area dove il lavoratore presta servizio, come richiesto dalla piattaforma corsi
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)

    documento_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    documento_raw_extraction: Mapped[str | None] = mapped_column(String, nullable=True)

    creato_il: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    azienda: Mapped["Azienda"] = relationship(back_populates="lavoratori")
    assegnazioni: Mapped[list["Assegnazione"]] = relationship(back_populates="lavoratore")
