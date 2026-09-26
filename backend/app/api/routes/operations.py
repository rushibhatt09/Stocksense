"""Receipts, delivery orders and internal transfers.

All three are the same document with different endpoints of the move, which is
why they share one create, one validate and one cancel.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import DocStatus, DocType, LocationType
from app.models.inventory import Location, Product
from app.models.operations import Document, DocumentLine
from app.models.user import User
from app.schemas.operations import (
    VALID_MANUAL_STATUSES,
    DocumentIn,
    DocumentOut,
    DocumentPage,
    DocumentUpdate,
)
from app.services.ledger import (
    cancel_document,
    create_document,
    delete_document,
    validate_document,
    virtual_location,
)

router = APIRouter(prefix="/operations", tags=["operations"])

# Which side of the move the client does not have to name.
IMPLIED_SIDE = {
    DocType.RECEIPT: ("src", LocationType.VENDOR),
    DocType.DELIVERY: ("dest", LocationType.CUSTOMER),
    DocType.ADJUSTMENT: ("src", LocationType.ADJUSTMENT),
}


def _load(db: Session, document_id: int) -> Document:
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.lines).selectinload(DocumentLine.product))
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def _to_out(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        reference=document.reference,
        doc_type=document.doc_type,
        status=document.status,
        partner_name=document.partner_name,
        src_location=document.src_location,
        dest_location=document.dest_location,
        scheduled_at=document.scheduled_at,
        validated_at=document.validated_at,
        created_at=document.created_at,
        note=document.note,
        lines=[
            {
                "id": line.id,
                "product_id": line.product_id,
                "product_name": line.product.name,
                "sku": line.product.sku,
                "uom": line.product.uom,
                "qty_demand": line.qty_demand,
                "qty_done": line.qty_done,
            }
            for line in document.lines
        ],
    )


def _resolve_endpoints(db: Session, payload: DocumentIn) -> tuple[int, int]:
    """Fill in the side the client left out, and require the side it must give."""
    src_id, dest_id = payload.src_location_id, payload.dest_location_id

    if payload.doc_type in IMPLIED_SIDE:
        side, location_type = IMPLIED_SIDE[payload.doc_type]
        counterpart = virtual_location(db, location_type)
        if side == "src" and src_id is None:
            src_id = counterpart.id
        if side == "dest" and dest_id is None:
            dest_id = counterpart.id

    if src_id is None or dest_id is None:
        missing = "source" if src_id is None else "destination"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A {payload.doc_type} needs a {missing} location",
        )
    return src_id, dest_id


@router.get("", response_model=DocumentPage)
def list_operations(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    doc_type: str | None = Query(default=None, description="receipt, delivery, internal or adjustment"),
    status_filter: str | None = Query(default=None, alias="status"),
    warehouse_id: int | None = None,
    category_id: int | None = None,
    q: str | None = Query(default=None, description="Matches reference or partner name."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
) -> DocumentPage:
    src = aliased(Location)
    dest = aliased(Location)

    stmt = (
        select(Document)
        .join(src, src.id == Document.src_location_id)
        .join(dest, dest.id == Document.dest_location_id)
    )

    if doc_type:
        if doc_type not in DocType.ALL:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown document type '{doc_type}'",
            )
        stmt = stmt.where(Document.doc_type == doc_type)

    if status_filter:
        if status_filter not in DocStatus.ALL:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown status '{status_filter}'",
            )
        stmt = stmt.where(Document.status == status_filter)

    if warehouse_id is not None:
        # A document belongs to a warehouse if either end of the move is in it.
        stmt = stmt.where(or_(src.warehouse_id == warehouse_id, dest.warehouse_id == warehouse_id))

    if category_id is not None:
        stmt = stmt.where(
            Document.id.in_(
                select(DocumentLine.document_id)
                .join(Product, Product.id == DocumentLine.product_id)
                .where(Product.category_id == category_id)
            )
        )

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Document.reference.ilike(pattern), Document.partner_name.ilike(pattern))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # The list screens show the route and the line count, so the rows come back
    # whole rather than as a summary; eager loading keeps it to a few queries.
    documents = db.scalars(
        stmt.options(
            selectinload(Document.lines).selectinload(DocumentLine.product),
            selectinload(Document.src_location),
            selectinload(Document.dest_location),
        )
        .order_by(Document.created_at.desc(), Document.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return DocumentPage(
        items=[_to_out(document) for document in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_operation(
    payload: DocumentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    src_id, dest_id = _resolve_endpoints(db, payload)

    document = create_document(
        db,
        doc_type=payload.doc_type,
        src_location_id=src_id,
        dest_location_id=dest_id,
        lines=[(line.product_id, line.qty_demand) for line in payload.lines],
        created_by=current_user.id,
        partner_name=payload.partner_name,
        scheduled_at=payload.scheduled_at,
        note=payload.note,
    )
    return _to_out(_load(db, document.id))


@router.get("/{document_id}", response_model=DocumentOut)
def get_operation(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> DocumentOut:
    return _to_out(_load(db, document_id))


@router.patch("/{document_id}", response_model=DocumentOut)
def update_operation(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentOut:
    """Edit a document that has not been validated.

    qty_done is what was actually picked, which is how the pick and pack steps of
    a delivery are recorded before it is validated.
    """
    document = _load(db, document_id)
    if document.status in (DocStatus.DONE, DocStatus.CANCELED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{document.reference} is {document.status} and can no longer be edited",
        )

    changes = payload.model_dump(exclude_unset=True)

    if "status" in changes and changes["status"] is not None:
        if changes["status"] not in VALID_MANUAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Status can be set to draft, waiting or ready. Use validate to "
                    "complete the document and cancel to drop it."
                ),
            )
        document.status = changes["status"]

    for field in ("partner_name", "scheduled_at", "note"):
        if field in changes:
            setattr(document, field, changes[field])

    if payload.lines is not None:
        for line in payload.lines:
            if db.get(Product, line.product_id) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {line.product_id} does not exist",
                )
        document.lines = [
            DocumentLine(
                product_id=line.product_id,
                qty_demand=line.qty_demand,
                qty_done=line.qty_done,
            )
            for line in payload.lines
        ]

    db.commit()
    return _to_out(_load(db, document_id))


@router.post("/{document_id}/validate", response_model=DocumentOut)
def validate_operation(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """Write the document's moves to the ledger. Stock changes here and nowhere else."""
    document = _load(db, document_id)
    validate_document(db, document, current_user.id)
    return _to_out(_load(db, document_id))


@router.post("/{document_id}/cancel", response_model=DocumentOut)
def cancel_operation(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> DocumentOut:
    document = _load(db, document_id)
    cancel_document(db, document)
    return _to_out(_load(db, document_id))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> None:
    """Drop a document that was never validated."""
    delete_document(db, _load(db, document_id))


# The same handlers mounted a second time at /documents, because the operations
# API was built under both names during the hackathon. One engine, two URLs:
# the logic exists once and both spellings stay valid.
documents_router = APIRouter(prefix="/documents", tags=["documents"])
for _route in list(router.routes):
    documents_router.add_api_route(
        _route.path.removeprefix(router.prefix) or "",
        _route.endpoint,
        methods=sorted(_route.methods),
        response_model=_route.response_model,
        status_code=_route.status_code,
        name=f"documents_{_route.name}",
    )
