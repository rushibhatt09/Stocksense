"""Warehouses and, nested under them, their locations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.inventory import Location, Warehouse
from app.schemas.inventory import LocationOut, WarehouseIn, WarehouseOut

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(select(Warehouse).order_by(Warehouse.name)).all()


@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseIn, db: Session = Depends(get_db), _=Depends(get_current_manager)
):
    if db.scalar(select(Warehouse).where(Warehouse.code == payload.code)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A warehouse with this code already exists")
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    return warehouse


@router.put("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseIn,
    db: Session = Depends(get_db),
    _=Depends(get_current_manager),
):
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    warehouse.name = payload.name
    warehouse.code = payload.code
    warehouse.address = payload.address
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    db.delete(warehouse)
    db.commit()


@router.get("/{warehouse_id}/locations", response_model=list[LocationOut])
def list_warehouse_locations(
    warehouse_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)
):
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    return db.scalars(
        select(Location).where(Location.warehouse_id == warehouse_id).order_by(Location.name)
    ).all()
