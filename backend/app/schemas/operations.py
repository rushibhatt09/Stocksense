"""Request and response bodies for receipts, deliveries, transfers and adjustments."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocStatus


class DocumentLineIn(BaseModel):
    product_id: int
    qty_demand: Decimal = Field(gt=0)


class DocumentLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    sku: str
    uom: str
    qty_demand: Decimal
    qty_done: Decimal


class DocumentIn(BaseModel):
    """Source and destination are optional where the system already knows one side.

    A receipt comes from Vendors, a delivery goes to Customers: the client only
    names the warehouse location it cares about.
    """

    doc_type: str
    partner_name: str | None = Field(default=None, max_length=180)
    src_location_id: int | None = None
    dest_location_id: int | None = None
    scheduled_at: datetime | None = None
    note: str | None = None
    lines: list[DocumentLineIn] = Field(min_length=1)


class DocumentUpdate(BaseModel):
    partner_name: str | None = None
    scheduled_at: datetime | None = None
    note: str | None = None
    status: str | None = None
    # Replaces the lines wholesale. qty_done is what was actually picked.
    lines: list["DocumentLinePatch"] | None = None


class DocumentLinePatch(BaseModel):
    product_id: int
    qty_demand: Decimal = Field(gt=0)
    qty_done: Decimal = Field(default=Decimal(0), ge=0)


class LocationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    type: str


class DocumentOut(BaseModel):
    id: int
    reference: str
    doc_type: str
    status: str
    partner_name: str | None
    src_location: LocationBrief
    dest_location: LocationBrief
    scheduled_at: datetime | None
    validated_at: datetime | None
    created_at: datetime
    note: str | None
    lines: list[DocumentLineOut]


class DocumentSummary(BaseModel):
    id: int
    reference: str
    doc_type: str
    status: str
    partner_name: str | None
    src_location_name: str
    dest_location_name: str
    scheduled_at: datetime | None
    validated_at: datetime | None
    created_at: datetime
    line_count: int
    total_qty: Decimal


class DocumentPage(BaseModel):
    items: list[DocumentSummary]
    total: int
    page: int
    page_size: int


class AdjustmentIn(BaseModel):
    """A physical count. The system works out the difference itself."""

    product_id: int
    location_id: int
    counted_qty: Decimal = Field(ge=0)
    reason: str | None = Field(default=None, max_length=255)


class MoveOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    uom: str
    qty: Decimal
    from_location_name: str
    to_location_name: str
    done_at: datetime
    document_id: int | None
    reference: str | None
    doc_type: str | None


class MovePage(BaseModel):
    items: list[MoveOut]
    total: int
    page: int
    page_size: int


VALID_MANUAL_STATUSES = (DocStatus.DRAFT, DocStatus.WAITING, DocStatus.READY)

DocumentUpdate.model_rebuild()
