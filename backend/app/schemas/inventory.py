"""Request and response bodies for products, categories, warehouses and locations."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: int | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None


class WarehouseIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=20)
    address: str | None = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    address: str | None = None


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=40)
    warehouse_id: int | None = None
    parent_id: int | None = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    type: str
    warehouse_id: int | None = None
    parent_id: int | None = None


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    sku: str = Field(min_length=1, max_length=60)
    category_id: int | None = None
    uom: str = Field(default="Unit", max_length=20)
    barcode: str | None = Field(default=None, max_length=60)
    reorder_point: Decimal = Field(default=Decimal(0), ge=0)
    reorder_qty: Decimal = Field(default=Decimal(0), ge=0)
    # Optional opening stock, recorded as an adjustment so it lands in the ledger
    # like every other quantity.
    initial_stock: Decimal | None = Field(default=None, ge=0)
    initial_location_id: int | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    category_id: int | None = None
    uom: str | None = Field(default=None, max_length=20)
    barcode: str | None = Field(default=None, max_length=60)
    reorder_point: Decimal | None = Field(default=None, ge=0)
    reorder_qty: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category_id: int | None
    category_name: str | None = None
    uom: str
    barcode: str | None
    reorder_point: Decimal
    reorder_qty: Decimal
    is_active: bool
    on_hand: Decimal = Decimal(0)
    is_low_stock: bool = False


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class LocationStockOut(BaseModel):
    location_id: int
    location_name: str
    location_code: str
    location_type: str
    warehouse_name: str | None
    on_hand: Decimal


class ProductStockOut(BaseModel):
    product_id: int
    sku: str
    name: str
    uom: str
    total_on_hand: Decimal
    by_location: list[LocationStockOut]
