"""Request/response bodies for documents (receipts, deliveries, internal
transfers, adjustments) and the stock-move ledger they produce when validated."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inventory import LocationBasic, ProductBasic


class DocumentLineIn(BaseModel):
    product_id: int
    qty: float = Field(gt=0)


class DocumentLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductBasic
    qty_demand: float
    qty_done: float


class DocumentCreateIn(BaseModel):
    doc_type: str
    partner_name: str | None = None
    src_location_id: int
    dest_location_id: int
    scheduled_at: datetime | None = None
    note: str | None = None
    lines: list[DocumentLineIn] = Field(min_length=1)


class DocumentUpdateIn(BaseModel):
    partner_name: str | None = None
    scheduled_at: datetime | None = None
    note: str | None = None
    lines: list[DocumentLineIn] | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    doc_type: str
    status: str
    partner_name: str | None
    src_location: LocationBasic
    dest_location: LocationBasic
    scheduled_at: datetime | None
    validated_at: datetime | None
    created_by: int | None
    note: str | None
    lines: list[DocumentLineOut]


class StockMoveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int | None
    product: ProductBasic
    from_location: LocationBasic
    to_location: LocationBasic
    qty: float
    done_at: datetime
