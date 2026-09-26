"""Stock-on-hand calculations, derived entirely from the append-only stock_moves
ledger. There is no `quantity` column anywhere else in the schema — every number
this module returns is a sum over moves, computed fresh each time it's asked for.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import LocationType
from app.models.inventory import Location
from app.models.operations import StockMove


def stock_on_hand(db: Session, product_id: int, location_id: int | None = None) -> float:
    """On-hand quantity for a product.

    With `location_id`, the balance at that single location. Without it, the
    balance across every physical (internal) location — i.e. total company-wide
    stock, ignoring the virtual vendor/customer/adjustment/scrap counterparts.
    """
    to_stmt = select(func.coalesce(func.sum(StockMove.qty), 0)).where(
        StockMove.product_id == product_id
    )
    from_stmt = select(func.coalesce(func.sum(StockMove.qty), 0)).where(
        StockMove.product_id == product_id
    )

    if location_id is not None:
        to_stmt = to_stmt.where(StockMove.to_location_id == location_id)
        from_stmt = from_stmt.where(StockMove.from_location_id == location_id)
    else:
        internal_ids = select(Location.id).where(Location.type == LocationType.INTERNAL)
        to_stmt = to_stmt.where(StockMove.to_location_id.in_(internal_ids))
        from_stmt = from_stmt.where(StockMove.from_location_id.in_(internal_ids))

    incoming = db.scalar(to_stmt) or 0
    outgoing = db.scalar(from_stmt) or 0
    return float(incoming) - float(outgoing)


def stock_by_location(db: Session, product_id: int) -> list[dict]:
    """Non-zero on-hand balances for a product, one row per physical location."""
    internal_locations = db.scalars(
        select(Location).where(Location.type == LocationType.INTERNAL).order_by(Location.name)
    ).all()

    rows = []
    for location in internal_locations:
        qty = stock_on_hand(db, product_id, location.id)
        if qty:
            rows.append({"location": location, "on_hand": qty})
    return rows


def bulk_on_hand(db: Session, product_ids: list[int] | None = None) -> dict[int, float]:
    """On-hand quantity (across internal locations) for many products at once.

    Two grouped queries instead of N calls to `stock_on_hand` — used by the
    product list and the dashboard, which need every product's balance together.
    """
    internal_ids = select(Location.id).where(Location.type == LocationType.INTERNAL)

    incoming_stmt = (
        select(StockMove.product_id, func.sum(StockMove.qty))
        .where(StockMove.to_location_id.in_(internal_ids))
        .group_by(StockMove.product_id)
    )
    outgoing_stmt = (
        select(StockMove.product_id, func.sum(StockMove.qty))
        .where(StockMove.from_location_id.in_(internal_ids))
        .group_by(StockMove.product_id)
    )
    if product_ids is not None:
        if not product_ids:
            return {}
        incoming_stmt = incoming_stmt.where(StockMove.product_id.in_(product_ids))
        outgoing_stmt = outgoing_stmt.where(StockMove.product_id.in_(product_ids))

    totals: dict[int, float] = {}
    for product_id, qty in db.execute(incoming_stmt):
        totals[product_id] = totals.get(product_id, 0.0) + float(qty)
    for product_id, qty in db.execute(outgoing_stmt):
        totals[product_id] = totals.get(product_id, 0.0) - float(qty)
    return totals


def is_low_stock(on_hand: float, reorder_point: float) -> bool:
    return on_hand <= float(reorder_point)
