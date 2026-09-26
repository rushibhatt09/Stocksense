from fastapi.testclient import TestClient


def test_manager_can_create_category(client: TestClient, manager_headers: dict[str, str]) -> None:
    response = client.post("/categories", json={"name": "Raw Material"}, headers=manager_headers)
    assert response.status_code == 201, response.text
    assert response.json()["name"] == "Raw Material"


def test_staff_cannot_create_category(client: TestClient, staff_headers: dict[str, str]) -> None:
    response = client.post("/categories", json={"name": "Raw Material"}, headers=staff_headers)
    assert response.status_code == 403


def test_duplicate_category_name_rejected(
    client: TestClient, manager_headers: dict[str, str]
) -> None:
    client.post("/categories", json={"name": "Packaging"}, headers=manager_headers)
    response = client.post("/categories", json={"name": "Packaging"}, headers=manager_headers)
    assert response.status_code == 409


def test_manager_can_create_warehouse_and_location(
    client: TestClient, manager_headers: dict[str, str]
) -> None:
    warehouse = client.post(
        "/warehouses", json={"name": "Main Warehouse", "code": "WH1"}, headers=manager_headers
    )
    assert warehouse.status_code == 201, warehouse.text

    location = client.post(
        "/locations",
        json={
            "name": "Main Store",
            "code": "WH1/MAIN",
            "type": "internal",
            "warehouse_id": warehouse.json()["id"],
        },
        headers=manager_headers,
    )
    assert location.status_code == 201, location.text
    assert location.json()["warehouse_id"] == warehouse.json()["id"]

    listed = client.get(
        f"/warehouses/{warehouse.json()['id']}/locations", headers=manager_headers
    )
    assert listed.status_code == 200
    # Creating a warehouse also creates its default Main Store, so the one added
    # here is the second location, not the only one.
    codes = {location["code"] for location in listed.json()}
    assert codes == {"WH1/MAIN-STORE", "WH1/MAIN"}


def test_duplicate_warehouse_code_rejected(
    client: TestClient, manager_headers: dict[str, str]
) -> None:
    client.post("/warehouses", json={"name": "A", "code": "WH1"}, headers=manager_headers)
    response = client.post("/warehouses", json={"name": "B", "code": "WH1"}, headers=manager_headers)
    assert response.status_code == 409


def test_create_product_rejects_duplicate_sku(
    client: TestClient, manager_headers: dict[str, str]
) -> None:
    payload = {"name": "Steel Rods", "sku": "STL-001", "uom": "kg"}
    assert client.post("/products", json=payload, headers=manager_headers).status_code == 201
    response = client.post("/products", json=payload, headers=manager_headers)
    assert response.status_code == 409


def test_staff_cannot_create_product_but_can_list(
    client: TestClient, manager_headers: dict[str, str], staff_headers: dict[str, str]
) -> None:
    client.post(
        "/products", json={"name": "Steel Rods", "sku": "STL-001", "uom": "kg"}, headers=manager_headers
    )
    assert (
        client.post(
            "/products", json={"name": "X", "sku": "X-1", "uom": "Unit"}, headers=staff_headers
        ).status_code
        == 403
    )
    listed = client.get("/products", headers=staff_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    first = listed.json()["items"][0]
    assert first["on_hand"] == 0
    assert first["is_low_stock"] is True  # 0 on hand <= reorder_point 0


def test_product_stock_by_location(client: TestClient, manager_headers: dict[str, str]) -> None:
    warehouse = client.post(
        "/warehouses", json={"name": "Main Warehouse", "code": "WH1"}, headers=manager_headers
    ).json()
    main_store = client.post(
        "/locations",
        json={"name": "Main Store", "code": "WH1/MAIN", "type": "internal", "warehouse_id": warehouse["id"]},
        headers=manager_headers,
    ).json()
    client.post(
        "/locations", json={"name": "Adj", "code": "VIRT/ADJUST", "type": "adjustment"}, headers=manager_headers
    )

    product = client.post(
        "/products",
        json={
            "name": "Steel Rods",
            "sku": "STL-001",
            "uom": "kg",
            "initial_stock": 50,
            "initial_stock_location_id": main_store["id"],
        },
        headers=manager_headers,
    ).json()

    detail = client.get(f"/products/{product['id']}", headers=manager_headers).json()
    assert detail["on_hand"] == 50

    stock = client.get(f"/products/{product['id']}/stock", headers=manager_headers).json()
    assert stock["total_on_hand"] == 50
    assert len(stock["by_location"]) == 1
    assert stock["by_location"][0]["on_hand"] == 50
    assert stock["by_location"][0]["location_id"] == main_store["id"]


def test_low_stock_filter(client: TestClient, manager_headers: dict[str, str]) -> None:
    client.post(
        "/products",
        json={"name": "Plenty", "sku": "P-1", "uom": "Unit", "reorder_point": 5},
        headers=manager_headers,
    )
    client.post(
        "/products",
        json={"name": "Scarce", "sku": "P-2", "uom": "Unit", "reorder_point": 5},
        headers=manager_headers,
    )
    response = client.get("/products?low_stock=true", headers=manager_headers)
    assert response.status_code == 200
    # Both start at 0 on-hand, so both are "low stock" until stock arrives.
    assert response.json()["total"] == 2
