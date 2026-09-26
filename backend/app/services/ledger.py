"""The one place stock is written.

Creating a document records an intention; validating it appends rows to the
ledger. Receipts, deliveries, transfers and adjustments all go through
`validate_document`, which is why their numbers can never disagree.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import DocStatus, DocType, LocationType
from app.models.inventory import Location, Product
from app.models.operations import Document, DocumentLine, StockMove
from app.services.stock import on_hand

REFERENCE_DIGITS = 4


def get_location(db: Session, location_id: int) -> Location:
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} does not exist",
        )
    return location


def virtual_location(db: Session, location_type: str) -> Location:
    """The counterpart location for a given kind of move, e.g. Vendors."""
    location = db.scalar(select(Location).where(Location.type == location_type))
    if location is None:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The '{location_type}' location is missing. Run the seed script.",
        )
    return location


def _warehouse_prefix(src: Location, dest: Location) -> str:
    """Documents are numbered per warehouse, taken from whichever side is physical."""
    for location in (dest, src):
        if location.type in LocationType.PHYSICAL and location.warehouse is not None:
            return location.warehouse.code
    return "WH"


# What each operation is allowed to look like. Stock arrives from a vendor,
# leaves to a customer, moves between real locations, or is corrected against the
# adjustment location: anything else is a mistake worth refusing early.
SHAPES = {
    DocType.RECEIPT: ((LocationType.VENDOR,), LocationType.PHYSICAL),
    DocType.DELIVERY: (LocationType.PHYSICAL, (LocationType.CUSTOMER,)),
    DocType.INTERNAL: (LocationType.PHYSICAL, LocationType.PHYSICAL),
}


def _check_shape(doc_type: str, src: Location, dest: Location) -> None:
    if doc_type == DocType.ADJUSTMENT:
        # One end is the adjustment location, the other a real one; either way round.
        ends = {src.type, dest.type}
        if LocationType.ADJUSTMENT not in ends or not ends & set(LocationType.PHYSICAL):
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "An adjustment moves stock between a real location and the "
                    "Inventory Adjustment location"
                ),
            )
        return

    allowed_src, allowed_dest = SHAPES[doc_type]
    if src.type not in allowed_src or dest.type not in allowed_dest:
        expected = {
            DocType.RECEIPT: "from a vendor location into a real one",
            DocType.DELIVERY: "from a real location out to a customer location",
            DocType.INTERNAL: "between two real locations",
        }[doc_type]
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A {doc_type} moves stock {expected}",
        )


def next_reference(db: Session, doc_type: str, src: Location, dest: Location) -> str:
    prefix = f"{_warehouse_prefix(src, dest)}/{DocType.PREFIX[doc_type]}/"
    used = db.scalar(
        select(func.count()).select_from(Document).where(Document.reference.like(f"{prefix}%"))
    )
    return f"{prefix}{(used or 0) + 1:0{REFERENCE_DIGITS}d}"


def create_document(
    db: Session,
    *,
    doc_type: str,
    src_location_id: int,
    dest_location_id: int,
    lines: list[tuple[int, Decimal]],
    created_by: int | None = None,
    partner_name: str | None = None,
    scheduled_at: datetime | None = None,
    note: str | None = None,
    doc_status: str = DocStatus.DRAFT,
) -> Document:
    """Create a document and its lines. Nothing is written to the ledger yet."""
    if doc_type not in DocType.ALL:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown document type '{doc_type}'",
        )
    if not lines:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A document needs at least one line",
        )

    src = get_location(db, src_location_id)
    dest = get_location(db, dest_location_id)
    _check_shape(doc_type, src, dest)
    if src.id == dest.id:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source and destination must be different",
        )

    for product_id, qty in lines:
        if db.get(Product, product_id) is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} does not exist",
            )
        if qty < 0 or (qty == 0 and doc_type != DocType.ADJUSTMENT):
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Every line needs a quantity greater than zero",
            )

    document = Document(
        doc_type=doc_type,
        status=doc_status,
        partner_name=partner_name,
        src_location_id=src.id,
        dest_location_id=dest.id,
        scheduled_at=scheduled_at,
        created_by=created_by,
        note=note,
        lines=[
            DocumentLine(product_id=product_id, qty_demand=qty, qty_done=0)
            for product_id, qty in lines
        ],
    )

    # Two documents created in the same second would compute the same number, so
    # retry rather than fail the request.
    for attempt in range(5):
        document.reference = next_reference(db, doc_type, src, dest)
        db.add(document)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 4:
                raise
    db.refresh(document)
    return document


def _validate_adjustment(
    db: Session,
    document: Document,
    src: Location,
    dest: Location,
    now: datetime,
) -> None:
    """Apply a physical count: move the difference, in whichever direction it falls.

    The line quantity is what was counted, not what should move. The difference is
    worked out here, at validation time, so a count typed ten minutes ago cannot
    quietly overwrite stock that has moved since.
    """
    physical = src if src.type in LocationType.PHYSICAL else dest
    counterpart = dest if physical is src else src

    for line in document.lines:
        counted = Decimal(str(line.qty_demand))
        recorded = on_hand(db, line.product_id, physical.id)
        difference = counted - recorded

        if difference == 0:
            # Nothing moved, so nothing is written to the ledger.
            line.qty_done = Decimal(0)
            continue

        # A surplus flows in from the adjustment location, a shortfall flows back.
        from_id, to_id = (
            (counterpart.id, physical.id) if difference > 0 else (physical.id, counterpart.id)
        )
        line.qty_done = abs(difference)
        db.add(
            StockMove(
                document_id=document.id,
                product_id=line.product_id,
                from_location_id=from_id,
                to_location_id=to_id,
                qty=abs(difference),
                done_at=now,
            )
        )

    document.status = DocStatus.DONE
    document.validated_at = now
    db.commit()
    db.refresh(document)


def validate_document(db: Session, document: Document, user_id: int | None = None) -> Document:
    """Append the document's moves to the ledger and mark it done."""
    if document.status == DocStatus.DONE:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"{document.reference} has already been validated",
        )
    if document.status == DocStatus.CANCELED:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"{document.reference} was canceled and cannot be validated",
        )
    if not document.lines:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nothing to validate: the document has no lines",
        )

    src = get_location(db, document.src_location_id)
    dest = get_location(db, document.dest_location_id)
    now = datetime.now(UTC)

    if document.doc_type == DocType.ADJUSTMENT:
        _validate_adjustment(db, document, src, dest, now)
        return document

    for line in document.lines:
        # A line that was not picked falls back to the requested quantity.
        qty = Decimal(str(line.qty_done or 0)) or Decimal(str(line.qty_demand))
        if qty <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Every line needs a quantity greater than zero",
            )

        # Taking stock out of a real location can never leave less than nothing.
        if src.type in LocationType.PHYSICAL:
            available = on_hand(db, line.product_id, src.id)
            if qty > available:
                product = db.get(Product, line.product_id)
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=(
                        f"Only {available} {product.uom if product else ''} of "
                        f"{product.name if product else line.product_id} available at "
                        f"{src.name}, cannot move {qty}"
                    ).strip(),
                )

        line.qty_done = qty
        db.add(
            StockMove(
                document_id=document.id,
                product_id=line.product_id,
                from_location_id=document.src_location_id,
                to_location_id=document.dest_location_id,
                qty=qty,
                done_at=now,
            )
        )

    document.status = DocStatus.DONE
    document.validated_at = now
    if user_id is not None and document.created_by is None:
        document.created_by = user_id

    db.commit()
    db.refresh(document)
    return document


def cancel_document(db: Session, document: Document) -> Document:
    """Cancel a document that has not been validated. Validated stock is corrected
    with an adjustment, never by editing history."""
    if document.status == DocStatus.DONE:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=(
                f"{document.reference} is already validated. Correct it with an "
                "inventory adjustment so the ledger keeps its history."
            ),
        )
    document.status = DocStatus.CANCELED
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document: Document) -> None:
    """Remove a document that never moved stock. Validated ones are permanent."""
    if document.status == DocStatus.DONE:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=(
                f"{document.reference} is validated and part of the ledger. Correct it "
                "with an inventory adjustment instead."
            ),
        )
    db.delete(document)
    db.commit()


def record_adjustment(
    db: Session,
    *,
    product_id: int,
    location_id: int,
    counted_qty: Decimal,
    created_by: int | None = None,
    reason: str | None = None,
) -> Document:
    """Correct recorded stock to match a physical count.

    Returns the adjustment document. It carries no moves when the count already
    matched what was recorded, because nothing moved.
    """
    location = get_location(db, location_id)
    if location.type not in LocationType.PHYSICAL:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stock can only be counted at a real storage location",
        )

    counterpart = virtual_location(db, LocationType.ADJUSTMENT)
    document = create_document(
        db,
        doc_type=DocType.ADJUSTMENT,
        src_location_id=counterpart.id,
        dest_location_id=location_id,
        lines=[(product_id, counted_qty)],
        created_by=created_by,
        note=reason,
    )
    return validate_document(db, document, created_by)


def record_opening_stock(
    db: Session,
    *,
    product_id: int,
    location_id: int,
    qty: Decimal,
    created_by: int | None = None,
) -> Document:
    """Opening stock for a new product, recorded as a validated adjustment."""
    source = virtual_location(db, LocationType.ADJUSTMENT)
    document = create_document(
        db,
        doc_type=DocType.ADJUSTMENT,
        src_location_id=source.id,
        dest_location_id=location_id,
        lines=[(product_id, qty)],
        created_by=created_by,
        note="Opening stock",
    )
    return validate_document(db, document, created_by)
