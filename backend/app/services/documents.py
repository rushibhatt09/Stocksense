"""Document lifecycle: which location types a receipt/delivery/transfer/
adjustment must connect, reference numbering, and turning validated lines into
append-only stock moves.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import DocStatus, DocType, LocationType
from app.models.inventory import Location
from app.models.operations import Document, StockMove
from app.services.stock import stock_on_hand

# The location type each side of a document must be, keyed by doc_type.
# None means "must be a physical (internal) location" rather than one specific
# virtual type.
_EXPECTED_TYPES: dict[str, tuple[str | None, str | None]] = {
    DocType.RECEIPT: (LocationType.VENDOR, None),
    DocType.DELIVERY: (None, LocationType.CUSTOMER),
    DocType.INTERNAL: (None, None),
    DocType.ADJUSTMENT: (LocationType.ADJUSTMENT, None),
}


def _check_location_type(location: Location, expected: str | None, side: str) -> None:
    if expected is None:
        if not location.is_physical:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{side} location must be a physical (internal) location",
            )
    elif location.type != expected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{side} location must be of type '{expected}'",
        )


def validate_locations(doc_type: str, src: Location, dest: Location) -> None:
    """Enforce the source/destination shape for each operation type.

    Receipt: Vendor -> physical. Delivery: physical -> Customer.
    Internal transfer: physical -> a *different* physical. Adjustment: the
    Inventory Adjustment virtual location <-> the physical location being counted.
    """
    if doc_type not in DocType.ALL:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown document type")

    expected_src, expected_dest = _EXPECTED_TYPES[doc_type]
    _check_location_type(src, expected_src, "Source")
    _check_location_type(dest, expected_dest, "Destination")

    if doc_type == DocType.INTERNAL and src.id == dest.id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "An internal transfer needs two different locations",
        )


def generate_reference(db: Session, doc_type: str, src: Location, dest: Location) -> str:
    """e.g. WH1/IN/0001 — warehouse of whichever side is physical, then the
    per-doc-type prefix, then a running sequence."""
    physical = dest if dest.is_physical else src
    warehouse_code = physical.warehouse.code if physical.warehouse_id else "GEN"
    prefix = DocType.PREFIX[doc_type]
    count = (
        db.scalar(select(func.count()).select_from(Document).where(Document.doc_type == doc_type))
        or 0
    )
    return f"{warehouse_code}/{prefix}/{count + 1:04d}"


def validate_document(document: Document, db: Session) -> list[StockMove]:
    """Turn a document's lines into ledger entries and mark it Done.

    Raises HTTPException (400/422) if a business rule fails; the caller's
    transaction is left untouched in that case since nothing has been added yet.
    """
    if document.status == DocStatus.DONE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This document is already validated")
    if document.status == DocStatus.CANCELED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A canceled document cannot be validated")
    if not document.lines:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Add at least one line before validating")

    moves: list[StockMove] = []
    now = datetime.now(UTC)

    if document.doc_type == DocType.ADJUSTMENT:
        # Each line's qty_demand holds the freshly *counted* quantity. The
        # move direction depends on whether that's above or below what the
        # ledger currently says is on hand at the counted location.
        for line in document.lines:
            current = stock_on_hand(db, line.product_id, document.dest_location_id)
            diff = float(line.qty_demand) - current
            if diff == 0:
                line.qty_done = 0
                continue
            if diff > 0:
                from_id, to_id = document.src_location_id, document.dest_location_id
            else:
                from_id, to_id = document.dest_location_id, document.src_location_id
            qty = abs(diff)
            line.qty_done = qty
            moves.append(
                StockMove(
                    document_id=document.id,
                    product_id=line.product_id,
                    from_location_id=from_id,
                    to_location_id=to_id,
                    qty=qty,
                    done_at=now,
                )
            )
    else:
        for line in document.lines:
            qty = float(line.qty_done) if line.qty_done else float(line.qty_demand)
            if document.doc_type in (DocType.DELIVERY, DocType.INTERNAL):
                available = stock_on_hand(db, line.product_id, document.src_location_id)
                if available < qty:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Not enough stock of product #{line.product_id} at the source "
                        f"location (have {available}, need {qty})",
                    )
            line.qty_done = qty
            moves.append(
                StockMove(
                    document_id=document.id,
                    product_id=line.product_id,
                    from_location_id=document.src_location_id,
                    to_location_id=document.dest_location_id,
                    qty=qty,
                    done_at=now,
                )
            )

    db.add_all(moves)
    document.status = DocStatus.DONE
    document.validated_at = now
    db.commit()
    return moves
