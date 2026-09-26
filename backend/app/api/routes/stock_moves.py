"""Read-only view over the append-only stock ledger: Move History."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import DocType
from app.models.operations import Document, StockMove
from app.models.user import User
from app.schemas.operations import StockMoveOut

router = APIRouter(prefix="/stock-moves", tags=["stock-moves"])


@router.get("", response_model=list[StockMoveOut])
def list_stock_moves(
    product_id: int | None = None,
    location_id: int | None = None,
    document_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    doc_type: str | None = Query(
        default=None, description="receipt, delivery, internal or adjustment"
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(StockMove).options(
        selectinload(StockMove.product),
        selectinload(StockMove.from_location),
        selectinload(StockMove.to_location),
    )
    if product_id is not None:
        stmt = stmt.where(StockMove.product_id == product_id)
    if document_id is not None:
        stmt = stmt.where(StockMove.document_id == document_id)
    if location_id is not None:
        stmt = stmt.where(
            (StockMove.from_location_id == location_id) | (StockMove.to_location_id == location_id)
        )
    if doc_type is not None:
        if doc_type not in DocType.ALL:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown document type '{doc_type}'",
            )
        # The move itself has no type: it inherits the document that produced it.
        stmt = stmt.where(
            StockMove.document_id.in_(
                select(Document.id).where(Document.doc_type == doc_type)
            )
        )
    if from_date is not None:
        stmt = stmt.where(StockMove.done_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(StockMove.done_at <= to_date)

    return db.scalars(
        stmt.order_by(StockMove.done_at.desc(), StockMove.id.desc()).offset(offset).limit(limit)
    ).all()
