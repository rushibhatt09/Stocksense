"""What we keep stock of, and where the stock sits."""

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import LocationType


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    locations: Mapped[list["Location"]] = relationship(
        back_populates="warehouse", cascade="all, delete-orphan"
    )


class Location(TimestampMixin, Base):
    """A shelf, rack or bin inside a warehouse.

    Virtual locations (vendors, customers, adjustment, scrap) have no warehouse.
    They are the counterpart of every move that changes the total stock, which is
    what makes the ledger balance.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default=LocationType.INTERNAL, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    warehouse: Mapped["Warehouse | None"] = relationship(back_populates="locations")
    children: Mapped[list["Location"]] = relationship()

    @property
    def is_physical(self) -> bool:
        return self.type in LocationType.PHYSICAL


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    uom: Mapped[str] = mapped_column(String(20), default="Unit", nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # Low stock is on-hand <= reorder_point. reorder_qty is what we would order.
    reorder_point: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    reorder_qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped["Category | None"] = relationship(back_populates="products")
