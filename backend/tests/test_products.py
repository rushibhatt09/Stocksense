from decimal import Decimal

from fastapi.testclient import TestClient


def _location_id(client: TestClient, headers: dict[str, str], code: str) -> int:
    locations = client.get("/locations", headers=headers).json()
    return next(location["id"] for location in locations if location["code"] == code)


def test_products_require_authentication(client: TestClient) -> None:
    assert client.get("/products").status_code == 401


def test_seeded_products_are_listed(client: TestClient, auth_headers, seeded) -> None:
    response = client.get("/products", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 10
    assert len(body["items"]) == 10
    # Nothing has been received yet, so every product is at zero.
    assert all(Decimal(item["on_hand"]) == 0 for item in body["items"])


def test_sku_and_name_search(client: TestClient, auth_headers, seeded) -> None:
    by_sku = client.get("/products", headers=auth_headers, params={"q": "STL-ROD"}).json()
    assert by_sku["total"] == 1
    assert by_sku["items"][0]["sku"] == "STL-ROD-12"

    by_name = client.get("/products", headers=auth_headers, params={"q": "steel"}).json()
    assert by_name["total"] == 3

    # Search is case insensitive.
    assert client.get("/products", headers=auth_headers, params={"q": "STEEL"}).json()["total"] == 3


def test_category_filter(client: TestClient, auth_headers, seeded) -> None:
    categories = client.get("/categories", headers=auth_headers).json()
    consumables = next(c for c in categories if c["name"] == "Consumables")

    filtered = client.get(
        "/products", headers=auth_headers, params={"category_id": consumables["id"]}
    ).json()
    assert filtered["total"] == 3
    assert all(item["category_name"] == "Consumables" for item in filtered["items"])


def test_pagination(client: TestClient, auth_headers, seeded) -> None:
    first = client.get("/products", headers=auth_headers, params={"page_size": 4}).json()
    assert first["total"] == 10
    assert len(first["items"]) == 4

    second = client.get(
        "/products", headers=auth_headers, params={"page_size": 4, "page": 2}
    ).json()
    assert len(second["items"]) == 4
    assert {item["id"] for item in first["items"]}.isdisjoint(
        {item["id"] for item in second["items"]}
    )


def test_create_product(client: TestClient, auth_headers, seeded) -> None:
    response = client.post(
        "/products",
        headers=auth_headers,
        json={"name": "Copper Wire", "sku": "cu-wire-01", "uom": "m", "reorder_point": 20},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "CU-WIRE-01"  # normalised
    assert Decimal(body["on_hand"]) == 0
    assert body["is_low_stock"] is True  # zero stock is below a reorder point of 20


def test_duplicate_sku_is_rejected(client: TestClient, auth_headers, seeded) -> None:
    response = client.post(
        "/products", headers=auth_headers, json={"name": "Clash", "sku": "STL-ROD-12"}
    )
    assert response.status_code == 409


def test_create_product_with_opening_stock_writes_the_ledger(
    client: TestClient, auth_headers, seeded
) -> None:
    location_id = _location_id(client, auth_headers, "WH1/MAIN-STORE")

    created = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Brass Fitting",
            "sku": "BRS-FIT-01",
            "uom": "Unit",
            "initial_stock": 40,
            "initial_location_id": location_id,
        },
    ).json()
    assert Decimal(created["on_hand"]) == 40

    stock = client.get(f"/products/{created['id']}/stock", headers=auth_headers).json()
    assert Decimal(stock["total_on_hand"]) == 40
    assert len(stock["by_location"]) == 1
    assert stock["by_location"][0]["location_code"] == "WH1/MAIN-STORE"
    assert Decimal(stock["by_location"][0]["on_hand"]) == 40


def test_opening_stock_needs_a_location(client: TestClient, auth_headers, seeded) -> None:
    response = client.post(
        "/products",
        headers=auth_headers,
        json={"name": "No Location", "sku": "NO-LOC-01", "initial_stock": 10},
    )
    assert response.status_code == 422


def test_low_stock_filter(client: TestClient, auth_headers, seeded) -> None:
    location_id = _location_id(client, auth_headers, "WH1/MAIN-STORE")

    # Everything starts at zero, so everything with a reorder point is low.
    all_low = client.get("/products", headers=auth_headers, params={"low_stock": True}).json()
    assert all_low["total"] == 10

    stocked = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Well Stocked",
            "sku": "WELL-01",
            "reorder_point": 5,
            "initial_stock": 500,
            "initial_location_id": location_id,
        },
    ).json()

    low_now = client.get("/products", headers=auth_headers, params={"low_stock": True}).json()
    assert stocked["id"] not in {item["id"] for item in low_now["items"]}
    assert low_now["total"] == 10


def test_update_product(client: TestClient, auth_headers, seeded) -> None:
    product = client.get("/products", headers=auth_headers).json()["items"][0]

    response = client.patch(
        f"/products/{product['id']}",
        headers=auth_headers,
        json={"reorder_point": 999},
    )
    assert response.status_code == 200
    assert Decimal(response.json()["reorder_point"]) == 999
    assert response.json()["name"] == product["name"]  # untouched fields stay


def test_update_to_an_existing_sku_is_rejected(client: TestClient, auth_headers, seeded) -> None:
    items = client.get("/products", headers=auth_headers).json()["items"]
    response = client.patch(
        f"/products/{items[0]['id']}", headers=auth_headers, json={"sku": items[1]["sku"]}
    )
    assert response.status_code == 409


def test_deactivated_products_are_hidden_by_default(
    client: TestClient, auth_headers, seeded
) -> None:
    product = client.get("/products", headers=auth_headers).json()["items"][0]
    client.patch(f"/products/{product['id']}", headers=auth_headers, json={"is_active": False})

    assert client.get("/products", headers=auth_headers).json()["total"] == 9
    assert (
        client.get("/products", headers=auth_headers, params={"include_inactive": True}).json()[
            "total"
        ]
        == 10
    )


def test_unknown_product_is_404(client: TestClient, auth_headers) -> None:
    assert client.get("/products/9999", headers=auth_headers).status_code == 404
    assert client.get("/products/9999/stock", headers=auth_headers).status_code == 404
