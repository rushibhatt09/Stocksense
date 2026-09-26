"""Test fixtures: every test runs against its own empty SQLite database."""

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    from app.db.base import Base
    from app.db.session import get_db
    from app.main import app

    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()
    os.unlink(path)


@pytest.fixture()
def signed_up(client: TestClient) -> dict[str, str]:
    credentials = {
        "name": "Test Manager",
        "email": "manager@example.com",
        "password": "supersecret1",
        "role": "manager",
    }
    response = client.post("/auth/signup", json=credentials)
    assert response.status_code == 201, response.text
    return credentials


def _signup_and_login(client: TestClient, email: str, role: str) -> dict[str, str]:
    credentials = {"name": role.title(), "email": email, "password": "supersecret1", "role": role}
    assert client.post("/auth/signup", json=credentials).status_code == 201
    token = client.post(
        "/auth/login", json={"email": email, "password": credentials["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def manager_headers(client: TestClient) -> dict[str, str]:
    return _signup_and_login(client, "manager@example.com", "manager")


@pytest.fixture()
def staff_headers(client: TestClient) -> dict[str, str]:
    return _signup_and_login(client, "staff@example.com", "staff")


@pytest.fixture()
def warehouse_setup(client: TestClient, manager_headers: dict[str, str]) -> dict:
    """A warehouse with one physical location, plus the four virtual
    counterparts every receipt/delivery/transfer/adjustment balances against."""
    h = manager_headers
    warehouse = client.post(
        "/warehouses", json={"name": "Main Warehouse", "code": "WH1"}, headers=h
    ).json()
    main_store = client.post(
        "/locations",
        json={"name": "Main Store", "code": "WH1/MAIN", "type": "internal", "warehouse_id": warehouse["id"]},
        headers=h,
    ).json()
    rack_b = client.post(
        "/locations",
        json={"name": "Rack B", "code": "WH1/RACKB", "type": "internal", "warehouse_id": warehouse["id"]},
        headers=h,
    ).json()
    vendors = client.post(
        "/locations", json={"name": "Vendors", "code": "VIRT/VENDORS", "type": "vendor"}, headers=h
    ).json()
    customers = client.post(
        "/locations", json={"name": "Customers", "code": "VIRT/CUSTOMERS", "type": "customer"}, headers=h
    ).json()
    adjustment = client.post(
        "/locations",
        json={"name": "Inventory Adjustment", "code": "VIRT/ADJUST", "type": "adjustment"},
        headers=h,
    ).json()
    product = client.post(
        "/products",
        json={"name": "Steel Rods", "sku": "STL-001", "uom": "kg", "reorder_point": 20, "reorder_qty": 100},
        headers=h,
    ).json()
    return {
        "warehouse": warehouse,
        "main_store": main_store,
        "rack_b": rack_b,
        "vendors": vendors,
        "customers": customers,
        "adjustment": adjustment,
        "product": product,
    }


@pytest.fixture()
def auth_headers(client: TestClient, signed_up: dict[str, str]) -> dict[str, str]:
    token = client.post(
        "/auth/login", json={"email": signed_up["email"], "password": signed_up["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded(client: TestClient) -> None:
    """Warehouses, locations, categories and products, as the seed script creates them."""
    from app.db.session import get_db
    from app.main import app
    from app.seed import seed

    db = next(app.dependency_overrides[get_db]())
    try:
        seed(db)
    finally:
        db.close()
