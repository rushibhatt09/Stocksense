"""On-hand stock, derived from the ledger.

Every quantity in the application comes from here. A StockMove row means the
quantity left `from_location` and arrived at `to_location`, so the stock at a
location is the sum of what arrived minus the sum of what left. Expressing that
as one signed set of rows lets a single GROUP BY answer every question: stock per
product, per location, or in total.
"""

from decimal import Decimal

from sqlalchemy import Select, func, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Subquery

from app.models.enums import LocationType
from app.models.inventory import Location, Product, Warehouse
from app.models.operations import StockMove


def signed_moves() -> Subquery:
    """Each move as two signed rows: +qty where it arrived, -qty where it left."""
    arrivals = select(
        StockMove.product_id.label("product_id"),
        StockMove.to_location_id.label("location_id"),
        StockMove.qty.label("qty"),
    )
    departures = select(
        StockMove.product_id.label("product_id"),
        StockMove.from_location_id.label("location_id"),
        (-StockMove.qty).label("qty"),
    )
    return union_all(arrivals, departures).subquery("signed_moves")


def on_hand_by_product() -> Subquery:
    """Total on-hand per product, counting physical locations only.

    Stock sitting in a virtual location (vendors, customers, scrap) is not stock
    we hold, so it never counts towards on-hand.
    """
    moves = signed_moves()
    return (
        select(
            moves.c.product_id.label("product_id"),
            func.coalesce(func.sum(moves.c.qty), 0).label("on_hand"),
        )
        .join(Location, Location.id == moves.c.location_id)
        .where(Location.type.in_(LocationType.PHYSICAL))
        .group_by(moves.c.product_id)
        .subquery("on_hand_by_product")
    )


def on_hand_query(product_id: int | None = None) -> Select:
    """Per-location stock, optionally for one product. Empty locations are omitted."""
    moves = signed_moves()
    stmt = (
        select(
            moves.c.product_id,
            moves.c.location_id,
            func.sum(moves.c.qty).label("on_hand"),
        )
        .group_by(moves.c.product_id, moves.c.location_id)
        .having(func.sum(moves.c.qty) != 0)
    )
    if product_id is not None:
        stmt = stmt.where(moves.c.product_id == product_id)
    return stmt


def on_hand(db: Session, product_id: int, location_id: int) -> Decimal:
    """Stock of one product at one location. The number a validation checks against."""
    moves = signed_moves()
    total = db.scalar(
        select(func.coalesce(func.sum(moves.c.qty), 0)).where(
            moves.c.product_id == product_id, moves.c.location_id == location_id
        )
    )
    return Decimal(str(total or 0))


def on_hand_totals(db: Session, product_ids: list[int] | None = None) -> dict[int, Decimal]:
    """Total physical stock per product, as a map. Products with no moves are absent."""
    totals = on_hand_by_product()
    stmt = select(totals.c.product_id, totals.c.on_hand)
    if product_ids is not None:
        stmt = stmt.where(totals.c.product_id.in_(product_ids))
    return {row.product_id: Decimal(str(row.on_hand)) for row in db.execute(stmt)}


def stock_by_location(
    db: Session, product_id: int, physical_only: bool = True
) -> list[dict]:
    """Where a product's stock physically is, warehouse by warehouse.

    Virtual locations are excluded: the -40 sitting against "Inventory Adjustment"
    after an opening-stock entry explains where the 40 came from, which belongs in
    Move History, not in a list of where the goods are.
    """
    stock = on_hand_query(product_id).subquery("stock")
    query = (
        select(
            Location.id.label("location_id"),
            Location.name.label("location_name"),
            Location.code.label("location_code"),
            Location.type.label("location_type"),
            Warehouse.name.label("warehouse_name"),
            stock.c.on_hand,
        )
        .join(Location, Location.id == stock.c.location_id)
        .outerjoin(Warehouse, Warehouse.id == Location.warehouse_id)
        .order_by(Location.code.asc())
    )
    if physical_only:
        query = query.where(Location.type.in_(LocationType.PHYSICAL))
    return [dict(row._mapping) for row in db.execute(query)]


def low_stock_products(db: Session, limit: int | None = None) -> list[tuple[Product, Decimal]]:
    """Products at or below their reorder point, lowest first."""
    totals = on_hand_by_product()
    stmt = (
        select(Product, func.coalesce(totals.c.on_hand, 0).label("on_hand"))
        .outerjoin(totals, totals.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .where(func.coalesce(totals.c.on_hand, 0) <= Product.reorder_point)
        .order_by(func.coalesce(totals.c.on_hand, 0).asc(), Product.name.asc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return [(row[0], Decimal(str(row[1]))) for row in db.execute(stmt)]


# --- Compatibility helpers -------------------------------------------------
# The dashboard and Move History routes were written against these names. They
# sit on the same ledger queries above and return floats, which is all a KPI
# tile or a badge needs; anything that must be exact keeps using the Decimal
# functions above.


def stock_on_hand(db: Session, product_id: int, location_id: int | None = None) -> float:
    """On-hand for a product, at one location or across all physical locations."""
    if location_id is not None:
        return float(on_hand(db, product_id, location_id))
    return float(on_hand_totals(db, [product_id]).get(product_id, Decimal(0)))


def bulk_on_hand(db: Session, product_ids: list[int] | None = None) -> dict[int, float]:
    """On-hand for many products in one query, for list and dashboard screens."""
    return {
        product_id: float(total)
        for product_id, total in on_hand_totals(db, product_ids).items()
    }


def is_low_stock(on_hand_qty: float | Decimal, reorder_point: float | Decimal) -> bool:
    return float(on_hand_qty) <= float(reorder_point)
