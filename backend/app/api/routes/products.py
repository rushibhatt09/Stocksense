"""Products, their SKU search, and the stock derived from the ledger."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.inventory import Category, Product
from app.models.user import User
from app.schemas.inventory import ProductIn, ProductOut, ProductPage, ProductStockOut, ProductUpdate
from app.services.ledger import get_location, record_opening_stock
from app.services.stock import on_hand_by_product, on_hand_totals, stock_by_location

router = APIRouter(prefix="/products", tags=["products"])


def _to_out(product: Product, on_hand: Decimal, category_name: str | None) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        sku=product.sku,
        category_id=product.category_id,
        category_name=category_name,
        uom=product.uom,
        barcode=product.barcode,
        reorder_point=product.reorder_point,
        reorder_qty=product.reorder_qty,
        is_active=product.is_active,
        on_hand=on_hand,
        is_low_stock=on_hand <= Decimal(str(product.reorder_point)),
    )


@router.get("", response_model=ProductPage)
def list_products(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    q: str | None = Query(default=None, description="Matches name or SKU."),
    search: str | None = Query(default=None, description="Alias of q."),
    category_id: int | None = None,
    low_stock: bool = False,
    include_inactive: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
) -> ProductPage:
    totals = on_hand_by_product()
    stock = func.coalesce(totals.c.on_hand, 0)

    stmt = (
        select(Product, stock.label("on_hand"), Category.name.label("category_name"))
        .outerjoin(totals, totals.c.product_id == Product.id)
        .outerjoin(Category, Category.id == Product.category_id)
    )

    term = q or search
    if term:
        pattern = f"%{term.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(pattern), Product.sku.ilike(pattern)))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if low_stock:
        stmt = stmt.where(stock <= Product.reorder_point)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(Product.name.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    return ProductPage(
        items=[_to_out(row[0], Decimal(str(row[1])), row[2]) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager),
) -> ProductOut:
    sku = payload.sku.strip().upper()
    if db.scalar(select(Product).where(Product.sku == sku)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"SKU {sku} is already used"
        )
    if payload.category_id is not None and db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    opening = payload.initial_stock or Decimal(0)
    if opening > 0 and payload.initial_location_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose a location for the initial stock",
        )

    product = Product(
        name=payload.name.strip(),
        sku=sku,
        category_id=payload.category_id,
        uom=payload.uom,
        barcode=payload.barcode,
        reorder_point=payload.reorder_point,
        reorder_qty=payload.reorder_qty,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    if opening > 0 and payload.initial_location_id is not None:
        # Opening stock is an adjustment, so even day-one quantities are in the ledger.
        get_location(db, payload.initial_location_id)
        record_opening_stock(
            db,
            product_id=product.id,
            location_id=payload.initial_location_id,
            qty=opening,
            created_by=current_user.id,
        )

    on_hand = on_hand_totals(db, [product.id]).get(product.id, Decimal(0))
    category_name = product.category.name if product.category else None
    return _to_out(product, on_hand, category_name)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductOut:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    on_hand = on_hand_totals(db, [product_id]).get(product_id, Decimal(0))
    return _to_out(product, on_hand, product.category.name if product.category else None)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
) -> ProductOut:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    changes = payload.model_dump(exclude_unset=True)

    if "sku" in changes and changes["sku"] is not None:
        sku = changes["sku"].strip().upper()
        clash = db.scalar(select(Product).where(Product.sku == sku, Product.id != product_id))
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"SKU {sku} is already used"
            )
        changes["sku"] = sku

    if changes.get("category_id") is not None and db.get(Category, changes["category_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for field, value in changes.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    on_hand = on_hand_totals(db, [product_id]).get(product_id, Decimal(0))
    return _to_out(product, on_hand, product.category.name if product.category else None)


@router.get("/{product_id}/stock", response_model=ProductStockOut)
def product_stock(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductStockOut:
    """Where this product's stock sits. Totals count physical locations only."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return ProductStockOut(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        uom=product.uom,
        total_on_hand=on_hand_totals(db, [product_id]).get(product_id, Decimal(0)),
        by_location=stock_by_location(db, product_id),
    )
