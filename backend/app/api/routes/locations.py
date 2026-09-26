"""Locations: physical shelves/racks inside a warehouse, or the virtual
vendor/customer/adjustment/scrap counterparts stock moves balance against."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.inventory import Location, Warehouse
from app.schemas.inventory import LocationIn, LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
def list_locations(
    warehouse_id: int | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Location)
    if warehouse_id is not None:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    if type is not None:
        stmt = stmt.where(Location.type == type)
    return db.scalars(stmt.order_by(Location.name)).all()


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationIn, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    if db.scalar(select(Location).where(Location.code == payload.code)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A location with this code already exists")
    if payload.warehouse_id is not None and db.get(Warehouse, payload.warehouse_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")

    location = Location(**payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    return location


@router.put("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: int,
    payload: LocationIn,
    db: Session = Depends(get_db),
    _=Depends(get_current_manager),
):
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    for field, value in payload.model_dump().items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    db.delete(location)
    db.commit()
