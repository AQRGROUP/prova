from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Corso(Base):
    """Un corso erogabile dalla piattaforma (es. Formazione Generale Lavoratori)."""

    __tablename__ = "corsi"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_sku: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    nome: Mapped[str] = mapped_column(String(255))
    categoria: Mapped[str] = mapped_column(String(100))
    ore: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validita_mesi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)


class MansioneCorsoRule(Base):
    """Regola che associa un pattern di mansione/rischio ai corsi obbligatori.

    corsi_sku è una lista di codici_sku (o placeholder se non ancora assegnati)
    separati da virgola, così le regole restano leggibili/modificabili come seed
    senza dover gestire una tabella many-to-many separata per l'MVP.
    """

    __tablename__ = "mansione_corso_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    mansione_pattern: Mapped[str] = mapped_column(String(255))
    rischio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corsi_sku: Mapped[str] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
