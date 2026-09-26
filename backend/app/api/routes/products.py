"""Products: what the business stocks, and how much of it is on hand right now."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.enums import LocationType
from app.models.inventory import Location, Product
from app.models.operations import StockMove
from app.schemas.inventory import (
    ProductIn,
    ProductOut,
    ProductStockOut,
    ProductUpdate,
    StockByLocationOut,
)
from app.services.stock import bulk_on_hand, is_low_stock, stock_by_location, stock_on_hand

router = APIRouter(prefix="/products", tags=["products"])


def _with_stock(product: Product, on_hand: float) -> ProductStockOut:
    return ProductStockOut(
        **ProductOut.model_validate(product).model_dump(),
        on_hand=on_hand,
        is_low_stock=is_low_stock(on_hand, product.reorder_point),
    )


@router.get("", response_model=list[ProductStockOut])
def list_products(
    category_id: int | None = None,
    is_active: bool | None = None,
    low_stock: bool = False,
    search: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Product)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    if search:
        like = f"%{search}%"
        stmt = stmt.where((Product.name.ilike(like)) | (Product.sku.ilike(like)))

    products = db.scalars(stmt.order_by(Product.name)).all()
    on_hand = bulk_on_hand(db, [p.id for p in products])

    results = []
    for product in products:
        qty = on_hand.get(product.id, 0.0)
        if low_stock and not is_low_stock(qty, product.reorder_point):
            continue
        results.append(_with_stock(product, qty))
    return results


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductIn, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    if db.scalar(select(Product).where(Product.sku == payload.sku)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A product with this SKU already exists")

    data = payload.model_dump(exclude={"initial_stock", "initial_stock_location_id"})
    product = Product(**data)
    db.add(product)
    db.flush()

    if payload.initial_stock and payload.initial_stock > 0:
        if payload.initial_stock_location_id is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "initial_stock_location_id is required when initial_stock is set",
            )
        location = db.get(Location, payload.initial_stock_location_id)
        if location is None or location.type != LocationType.INTERNAL:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "initial_stock_location_id must be a physical (internal) location",
            )
        adjustment_location = db.scalar(
            select(Location).where(Location.type == LocationType.ADJUSTMENT)
        )
        if adjustment_location is None:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "No Inventory Adjustment virtual location is configured",
            )
        db.add(
            StockMove(
                document_id=None,
                product_id=product.id,
                from_location_id=adjustment_location.id,
                to_location_id=location.id,
                qty=payload.initial_stock,
                done_at=datetime.now(UTC),
            )
        )

    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductStockOut)
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return _with_stock(product, stock_on_hand(db, product_id))


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_manager),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    """Soft delete: archive the product. Its ledger history is never removed."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    product.is_active = False
    db.commit()


@router.get("/{product_id}/stock", response_model=list[StockByLocationOut])
def product_stock_by_location(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return stock_by_location(db, product_id)
