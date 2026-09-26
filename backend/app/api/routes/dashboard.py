"""Dashboard KPIs. Every number here is derived on the fly from the stock
ledger and the documents table — nothing is cached or stored separately, so
these can never drift from Products / Move History / Operations screens."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import DocStatus, DocType
from app.models.inventory import Product
from app.models.operations import Document
from app.models.user import User
from app.services.stock import bulk_on_hand, is_low_stock

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummary(BaseModel):
    total_products_in_stock: int
    low_stock_count: int
    out_of_stock_count: int
    pending_receipts: int
    pending_deliveries: int
    pending_transfers: int
    pending_adjustments: int


def _pending_count(db: Session, doc_type: str) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.doc_type == doc_type, Document.status.in_(DocStatus.OPEN))
        )
        or 0
    )


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = db.scalars(select(Product).where(Product.is_active.is_(True))).all()
    on_hand = bulk_on_hand(db, [p.id for p in products])

    total_in_stock = 0
    low_stock = 0
    out_of_stock = 0
    for product in products:
        qty = on_hand.get(product.id, 0.0)
        if qty > 0:
            total_in_stock += 1
            if is_low_stock(qty, product.reorder_point):
                low_stock += 1
        else:
            out_of_stock += 1

    return DashboardSummary(
        total_products_in_stock=total_in_stock,
        low_stock_count=low_stock,
        out_of_stock_count=out_of_stock,
        pending_receipts=_pending_count(db, DocType.RECEIPT),
        pending_deliveries=_pending_count(db, DocType.DELIVERY),
        pending_transfers=_pending_count(db, DocType.INTERNAL),
        pending_adjustments=_pending_count(db, DocType.ADJUSTMENT),
    )
