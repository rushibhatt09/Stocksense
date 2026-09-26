"""Seed the database with the structure StockSense needs plus demo data.

Idempotent: run it as often as you like. Codes and SKUs are the identity, so
re-running updates nothing and duplicates nothing.

    cd backend && python -m app.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import LocationType, Role
from app.models.inventory import Category, Location, Product, Warehouse
from app.models.user import User

# Virtual locations are the counterpart of every move that changes total stock.
VIRTUAL_LOCATIONS = [
    ("Vendors", "VIRT/VENDORS", LocationType.VENDOR),
    ("Customers", "VIRT/CUSTOMERS", LocationType.CUSTOMER),
    ("Inventory Adjustment", "VIRT/ADJUST", LocationType.ADJUSTMENT),
    ("Scrap", "VIRT/SCRAP", LocationType.SCRAP),
]

WAREHOUSES = [
    ("Main Warehouse", "WH1", "Plot 14, GIDC Industrial Estate", ["Main Store", "Production Rack", "Rack A", "Rack B"]),
    ("Secondary Warehouse", "WH2", "Survey 88, Ring Road", ["Main Store"]),
]

CATEGORIES = ["Raw Material", "Finished Goods", "Consumables", "Packaging"]

# name, sku, category, unit of measure, reorder point, reorder qty
PRODUCTS = [
    ("Steel Rods 12mm", "STL-ROD-12", "Raw Material", "kg", 50, 200),
    ("Steel Sheet 2mm", "STL-SHT-02", "Raw Material", "kg", 40, 150),
    ("Aluminium Profile", "ALU-PRF-01", "Raw Material", "m", 30, 120),
    ("Office Chair", "FRN-CHR-01", "Finished Goods", "Unit", 10, 40),
    ("Steel Frame Assembly", "FRM-ASM-01", "Finished Goods", "Unit", 8, 25),
    ("Welding Rods", "CNS-WLD-01", "Consumables", "Box", 5, 20),
    ("Cutting Discs", "CNS-CUT-01", "Consumables", "Box", 6, 24),
    ("Machine Oil 5L", "CNS-OIL-05", "Consumables", "Can", 4, 12),
    ("Carton Box Large", "PKG-BOX-L", "Packaging", "Unit", 100, 500),
    ("Stretch Wrap Roll", "PKG-WRP-01", "Packaging", "Roll", 12, 50),
]

DEMO_USERS = [
    ("Inventory Manager", "manager@stocksense.app", "manager123", Role.MANAGER),
    ("Warehouse Staff", "staff@stocksense.app", "staff123", Role.STAFF),
]


def _get_or_create_location(db: Session, code: str, **values) -> Location:
    location = db.scalar(select(Location).where(Location.code == code))
    if location is None:
        location = Location(code=code, **values)
        db.add(location)
    return location


def seed(db: Session) -> None:
    for name, code, loc_type in VIRTUAL_LOCATIONS:
        _get_or_create_location(db, code, name=name, type=loc_type, warehouse_id=None)

    for name, code, address, location_names in WAREHOUSES:
        warehouse = db.scalar(select(Warehouse).where(Warehouse.code == code))
        if warehouse is None:
            warehouse = Warehouse(name=name, code=code, address=address)
            db.add(warehouse)
            db.flush()
        for location_name in location_names:
            slug = location_name.upper().replace(" ", "-")
            _get_or_create_location(
                db,
                f"{code}/{slug}",
                name=location_name,
                type=LocationType.INTERNAL,
                warehouse_id=warehouse.id,
            )

    categories: dict[str, Category] = {}
    for name in CATEGORIES:
        category = db.scalar(select(Category).where(Category.name == name))
        if category is None:
            category = Category(name=name)
            db.add(category)
            db.flush()
        categories[name] = category

    for name, sku, category_name, uom, reorder_point, reorder_qty in PRODUCTS:
        if db.scalar(select(Product).where(Product.sku == sku)) is None:
            db.add(
                Product(
                    name=name,
                    sku=sku,
                    category_id=categories[category_name].id,
                    uom=uom,
                    reorder_point=reorder_point,
                    reorder_qty=reorder_qty,
                )
            )

    for name, email, password, role in DEMO_USERS:
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                )
            )

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    print("Seed complete.")
    print("  manager@stocksense.app / manager123")
    print("  staff@stocksense.app   / staff123")


if __name__ == "__main__":
    main()
