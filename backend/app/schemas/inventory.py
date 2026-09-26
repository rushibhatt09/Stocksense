"""Request/response bodies for products, categories, warehouses and locations."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LocationType


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: int | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None


class WarehouseIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=20)
    address: str | None = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    address: str | None


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=40)
    type: str = LocationType.INTERNAL
    warehouse_id: int | None = None
    parent_id: int | None = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    type: str
    warehouse_id: int | None
    parent_id: int | None


class LocationBasic(BaseModel):
    """Minimal location info nested inside documents and stock moves."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    type: str


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    sku: str = Field(min_length=1, max_length=60)
    category_id: int | None = None
    uom: str = "Unit"
    barcode: str | None = None
    reorder_point: float = Field(default=0, ge=0)
    reorder_qty: float = Field(default=0, ge=0)
    # Optional convenience: seed on-hand stock at a location when creating the
    # product, instead of requiring a separate receipt for the opening balance.
    initial_stock: float = Field(default=0, ge=0)
    initial_stock_location_id: int | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    uom: str | None = None
    barcode: str | None = None
    reorder_point: float | None = Field(default=None, ge=0)
    reorder_qty: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category_id: int | None
    uom: str
    barcode: str | None
    reorder_point: float
    reorder_qty: float
    is_active: bool


class ProductStockOut(ProductOut):
    """A product plus its derived, ledger-computed stock position."""

    on_hand: float
    is_low_stock: bool


class ProductBasic(BaseModel):
    """Minimal product info nested inside documents and stock moves."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    uom: str


class StockByLocationOut(BaseModel):
    location: LocationBasic
    on_hand: float
