"""Read-only view over the append-only stock ledger: Move History."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.operations import StockMove
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
    if from_date is not None:
        stmt = stmt.where(StockMove.done_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(StockMove.done_at <= to_date)

    return db.scalars(stmt.order_by(StockMove.done_at.desc(), StockMove.id.desc())).all()
