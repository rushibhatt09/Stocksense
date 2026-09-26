"""Categories, warehouses and locations: the structure products and moves refer to."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.enums import LocationType
from app.models.inventory import Category, Location, Warehouse
from app.models.user import User
from app.schemas.inventory import (
    CategoryIn,
    CategoryOut,
    LocationIn,
    LocationOut,
    WarehouseIn,
    WarehouseOut,
)

router = APIRouter(tags=["catalog"], dependencies=[Depends(get_current_user)])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


@router.post("/categories", dependencies=[Depends(get_current_manager)], response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryIn, db: Session = Depends(get_db)) -> Category:
    if db.scalar(select(Category).where(Category.name == payload.name)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="That category already exists"
        )
    category = Category(name=payload.name, parent_id=payload.parent_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)) -> list[Warehouse]:
    return list(db.scalars(select(Warehouse).order_by(Warehouse.code)))


@router.post("/warehouses", dependencies=[Depends(get_current_manager)], response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_warehouse(payload: WarehouseIn, db: Session = Depends(get_db)) -> Warehouse:
    code = payload.code.upper()
    if db.scalar(select(Warehouse).where(Warehouse.code == code)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Warehouse code {code} is already used"
        )

    warehouse = Warehouse(name=payload.name, code=code, address=payload.address)
    db.add(warehouse)
    db.flush()
    # A warehouse with no location cannot hold stock, so give it a default one.
    db.add(
        Location(
            name="Main Store",
            code=f"{code}/MAIN-STORE",
            type=LocationType.INTERNAL,
            warehouse_id=warehouse.id,
        )
    )
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/warehouses/{warehouse_id}/locations", response_model=list[LocationOut])
def list_warehouse_locations(
    warehouse_id: int, db: Session = Depends(get_db)
) -> list[Location]:
    """The locations inside one warehouse."""
    if db.get(Warehouse, warehouse_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return list(
        db.scalars(
            select(Location).where(Location.warehouse_id == warehouse_id).order_by(Location.code)
        )
    )


@router.get("/locations", response_model=list[LocationOut])
def list_locations(
    db: Session = Depends(get_db),
    warehouse_id: int | None = None,
    physical_only: bool = Query(
        default=True,
        description="Exclude vendor, customer, adjustment and scrap locations.",
    ),
) -> list[Location]:
    stmt = select(Location).order_by(Location.code)
    if warehouse_id is not None:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    if physical_only:
        stmt = stmt.where(Location.type.in_(LocationType.PHYSICAL))
    return list(db.scalars(stmt))


@router.post("/locations", dependencies=[Depends(get_current_manager)], response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationIn, db: Session = Depends(get_db)) -> Location:
    code = payload.code.upper()
    if db.scalar(select(Location).where(Location.code == code)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Location code {code} is already used"
        )
    if payload.warehouse_id is not None and db.get(Warehouse, payload.warehouse_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    if payload.type not in LocationType.ALL:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown location type '{payload.type}'",
        )

    location = Location(
        name=payload.name,
        code=code,
        type=payload.type,
        warehouse_id=payload.warehouse_id,
        parent_id=payload.parent_id,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location
