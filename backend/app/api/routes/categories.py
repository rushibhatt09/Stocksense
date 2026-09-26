"""Product categories: a simple, optionally hierarchical, tagging tree."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_manager, get_current_user
from app.db.session import get_db
from app.models.inventory import Category
from app.schemas.inventory import CategoryIn, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryIn, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    if db.scalar(select(Category).where(Category.name == payload.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A category with this name already exists")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryIn,
    db: Session = Depends(get_db),
    _=Depends(get_current_manager),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    category.name = payload.name
    category.parent_id = payload.parent_id
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db), _=Depends(get_current_manager)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    db.delete(category)
    db.commit()
