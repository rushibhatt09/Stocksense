"""Receipts, deliveries, internal transfers and adjustments — all one Document
model, distinguished by doc_type, all producing rows in the stock ledger when
validated. See app.services.documents for the workflow rules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import DocStatus, DocType
from app.models.inventory import Location, Product
from app.models.operations import Document, DocumentLine
from app.models.user import User
from app.schemas.operations import DocumentCreateIn, DocumentOut, DocumentUpdateIn
from app.services.documents import generate_reference, validate_document, validate_locations

router = APIRouter(prefix="/documents", tags=["documents"])


def _loaded(stmt):
    return stmt.options(
        selectinload(Document.lines).selectinload(DocumentLine.product),
        selectinload(Document.src_location),
        selectinload(Document.dest_location),
    )


def _get_document_or_404(document_id: int, db: Session) -> Document:
    document = db.scalar(_loaded(select(Document).where(Document.id == document_id)))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document


def _get_locations(db: Session, src_id: int, dest_id: int) -> tuple[Location, Location]:
    src = db.get(Location, src_id)
    dest = db.get(Location, dest_id)
    if src is None or dest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source or destination location not found")
    return src, dest


@router.get("", response_model=list[DocumentOut])
def list_documents(
    doc_type: str | None = None,
    status_: str | None = Query(default=None, alias="status"),
    warehouse_id: int | None = None,
    location_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = _loaded(select(Document))
    if doc_type is not None:
        stmt = stmt.where(Document.doc_type == doc_type)
    if status_ is not None:
        stmt = stmt.where(Document.status == status_)
    if location_id is not None:
        stmt = stmt.where(
            (Document.src_location_id == location_id) | (Document.dest_location_id == location_id)
        )
    if warehouse_id is not None:
        warehouse_location_ids = select(Location.id).where(Location.warehouse_id == warehouse_id)
        stmt = stmt.where(
            Document.src_location_id.in_(warehouse_location_ids)
            | Document.dest_location_id.in_(warehouse_location_ids)
        )
    return db.scalars(stmt.order_by(Document.id.desc())).all()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.doc_type not in DocType.ALL:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown document type")

    src, dest = _get_locations(db, payload.src_location_id, payload.dest_location_id)
    validate_locations(payload.doc_type, src, dest)

    for line in payload.lines:
        if db.get(Product, line.product_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Product #{line.product_id} not found")

    document = Document(
        reference=generate_reference(db, payload.doc_type, src, dest),
        doc_type=payload.doc_type,
        status=DocStatus.DRAFT,
        partner_name=payload.partner_name,
        src_location_id=src.id,
        dest_location_id=dest.id,
        scheduled_at=payload.scheduled_at,
        note=payload.note,
        created_by=current_user.id,
    )
    document.lines = [
        DocumentLine(product_id=line.product_id, qty_demand=line.qty, qty_done=0)
        for line in payload.lines
    ]
    db.add(document)
    db.commit()
    return _get_document_or_404(document.id, db)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_document_or_404(document_id, db)


@router.put("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int,
    payload: DocumentUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    document = _get_document_or_404(document_id, db)
    if document.status not in (DocStatus.DRAFT, DocStatus.WAITING):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only draft or waiting documents can be edited"
        )

    if payload.partner_name is not None:
        document.partner_name = payload.partner_name
    if payload.scheduled_at is not None:
        document.scheduled_at = payload.scheduled_at
    if payload.note is not None:
        document.note = payload.note
    if payload.lines is not None:
        for line in payload.lines:
            if db.get(Product, line.product_id) is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, f"Product #{line.product_id} not found"
                )
        document.lines = [
            DocumentLine(product_id=line.product_id, qty_demand=line.qty, qty_done=0)
            for line in payload.lines
        ]

    db.commit()
    return _get_document_or_404(document_id, db)


@router.post("/{document_id}/validate", response_model=DocumentOut)
def validate(document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    document = _get_document_or_404(document_id, db)
    validate_document(document, db)
    return _get_document_or_404(document_id, db)


@router.post("/{document_id}/cancel", response_model=DocumentOut)
def cancel_document(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    document = _get_document_or_404(document_id, db)
    if document.status == DocStatus.DONE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A validated document cannot be canceled")
    document.status = DocStatus.CANCELED
    db.commit()
    return _get_document_or_404(document_id, db)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    document = _get_document_or_404(document_id, db)
    if document.status != DocStatus.DRAFT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only draft documents can be deleted")
    db.delete(document)
    db.commit()
