"""Documents (receipts, deliveries, transfers, adjustments) and the stock ledger.

A document is an intention: these products, this quantity, from here to there.
Validating it writes StockMove rows, and those rows are the only source of truth
for how much stock exists. Nothing else stores a quantity.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import DocStatus
from app.models.inventory import Location, Product


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=DocStatus.DRAFT, index=True, nullable=False
    )
    # Supplier for a receipt, customer for a delivery; empty for internal moves.
    partner_name: Mapped[str | None] = mapped_column(String(180), nullable=True)

    src_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    dest_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    src_location: Mapped["Location"] = relationship(foreign_keys=[src_location_id])
    dest_location: Mapped["Location"] = relationship(foreign_keys=[dest_location_id])
    lines: Mapped[list["DocumentLine"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentLine.id"
    )
    moves: Mapped[list["StockMove"]] = relationship(back_populates="document")


class DocumentLine(Base):
    __tablename__ = "document_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    qty_demand: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    qty_done: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="lines")
    product: Mapped["Product"] = relationship()


class StockMove(Base):
    """One row of the stock ledger. Append only: never updated, never deleted.

    A mistake is corrected by adding the opposite move, exactly like an
    accounting ledger, so the history always explains the current stock.
    """

    __tablename__ = "stock_moves"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    to_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    done_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="moves")
    product: Mapped["Product"] = relationship()
    from_location: Mapped["Location"] = relationship(foreign_keys=[from_location_id])
    to_location: Mapped["Location"] = relationship(foreign_keys=[to_location_id])
