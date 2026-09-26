from fastapi.testclient import TestClient


def test_catalog_requires_authentication(client: TestClient) -> None:
    assert client.get("/warehouses").status_code == 401
    assert client.get("/locations").status_code == 401
    assert client.get("/categories").status_code == 401


def test_locations_hide_virtual_ones_by_default(client: TestClient, auth_headers, seeded) -> None:
    physical = client.get("/locations", headers=auth_headers).json()
    assert {location["type"] for location in physical} == {"internal"}
    assert len(physical) == 5  # 4 in WH1, 1 in WH2

    everything = client.get(
        "/locations", headers=auth_headers, params={"physical_only": False}
    ).json()
    types = {location["type"] for location in everything}
    assert {"vendor", "customer", "adjustment", "scrap"} <= types


def test_locations_can_be_filtered_by_warehouse(client: TestClient, auth_headers, seeded) -> None:
    warehouses = client.get("/warehouses", headers=auth_headers).json()
    wh1 = next(w for w in warehouses if w["code"] == "WH1")

    locations = client.get(
        "/locations", headers=auth_headers, params={"warehouse_id": wh1["id"]}
    ).json()
    assert len(locations) == 4
    assert all(location["warehouse_id"] == wh1["id"] for location in locations)


def test_creating_a_warehouse_also_creates_a_default_location(
    client: TestClient, auth_headers, seeded
) -> None:
    created = client.post(
        "/warehouses", headers=auth_headers, json={"name": "Third Warehouse", "code": "wh3"}
    )
    assert created.status_code == 201
    assert created.json()["code"] == "WH3"  # normalised

    locations = client.get(
        "/locations", headers=auth_headers, params={"warehouse_id": created.json()["id"]}
    ).json()
    assert [location["code"] for location in locations] == ["WH3/MAIN-STORE"]


def test_duplicate_codes_are_rejected(client: TestClient, auth_headers, seeded) -> None:
    assert (
        client.post(
            "/warehouses", headers=auth_headers, json={"name": "Clash", "code": "WH1"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/locations", headers=auth_headers, json={"name": "Clash", "code": "WH1/RACK-A"}
        ).status_code
        == 409
    )


def test_create_location_in_a_warehouse(client: TestClient, auth_headers, seeded) -> None:
    warehouses = client.get("/warehouses", headers=auth_headers).json()
    response = client.post(
        "/locations",
        headers=auth_headers,
        json={"name": "Rack C", "code": "wh1/rack-c", "warehouse_id": warehouses[0]["id"]},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "WH1/RACK-C"
    assert response.json()["type"] == "internal"


def test_create_category(client: TestClient, auth_headers, seeded) -> None:
    assert (
        client.post("/categories", headers=auth_headers, json={"name": "Spare Parts"}).status_code
        == 201
    )
    assert (
        client.post("/categories", headers=auth_headers, json={"name": "Spare Parts"}).status_code
        == 409
    )
