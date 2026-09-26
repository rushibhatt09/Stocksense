"""Inventory adjustments: make recorded stock match a physical count."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.operations import AdjustmentIn, AdjustmentOut
from app.services.ledger import record_adjustment
from app.services.stock import on_hand

router = APIRouter(prefix="/adjustments", tags=["adjustments"])


@router.post("", response_model=AdjustmentOut, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    payload: AdjustmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Record a count. Only the difference moves, and a matching count moves nothing."""
    recorded = on_hand(db, payload.product_id, payload.location_id)

    document = record_adjustment(
        db,
        product_id=payload.product_id,
        location_id=payload.location_id,
        counted_qty=payload.counted_qty,
        created_by=current_user.id,
        reason=payload.reason,
    )

    difference = payload.counted_qty - recorded
    moved = bool(document.moves)

    return {
        "adjusted": moved,
        "message": (
            f"Stock corrected by {difference}."
            if moved
            else "The count matches the recorded stock, so nothing moved."
        ),
        "recorded_qty": recorded,
        "counted_qty": payload.counted_qty,
        "difference": difference,
        "reference": document.reference,
    }
