"""Receipts, deliveries and internal transfers, checked through the stock they move."""

from decimal import Decimal

from fastapi.testclient import TestClient


def location_id(client: TestClient, headers: dict[str, str], code: str) -> int:
    locations = client.get(
        "/locations", headers=headers, params={"physical_only": False}
    ).json()
    return next(location["id"] for location in locations if location["code"] == code)


def product_id(client: TestClient, headers: dict[str, str], sku: str) -> int:
    products = client.get("/products", headers=headers, params={"q": sku}).json()["items"]
    return next(product["id"] for product in products if product["sku"] == sku)


def on_hand(client: TestClient, headers: dict[str, str], pid: int) -> Decimal:
    return Decimal(client.get(f"/products/{pid}", headers=headers).json()["on_hand"])


def receive(
    client: TestClient, headers: dict[str, str], pid: int, qty, dest_code="WH1/MAIN-STORE"
) -> dict:
    """Receive stock and validate it, the usual way a test gets stock on hand."""
    created = client.post(
        "/operations",
        headers=headers,
        json={
            "doc_type": "receipt",
            "partner_name": "Gujarat Steel Co",
            "dest_location_id": location_id(client, headers, dest_code),
            "lines": [{"product_id": pid, "qty_demand": qty}],
        },
    )
    assert created.status_code == 201, created.text
    document = created.json()
    validated = client.post(f"/operations/{document['id']}/validate", headers=headers)
    assert validated.status_code == 200, validated.text
    return validated.json()


def test_operations_require_authentication(client: TestClient) -> None:
    assert client.get("/operations").status_code == 401
    assert client.post("/operations", json={}).status_code == 401


def test_receipt_defaults_its_source_to_vendors(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "receipt",
            "partner_name": "Gujarat Steel Co",
            "dest_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 100}],
        },
    )
    assert created.status_code == 201
    body = created.json()
    # The client never names the vendor location; the system knows it.
    assert body["src_location"]["type"] == "vendor"
    assert body["status"] == "draft"
    assert body["reference"].startswith("WH1/IN/")


def test_draft_receipt_does_not_change_stock(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "receipt",
            "dest_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 100}],
        },
    )
    # Stock moves on validation, never on creation.
    assert on_hand(client, auth_headers, pid) == 0


def test_validated_receipt_increases_stock(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    document = receive(client, auth_headers, pid, 100)

    assert document["status"] == "done"
    assert document["validated_at"] is not None
    assert Decimal(document["lines"][0]["qty_done"]) == 100
    assert on_hand(client, auth_headers, pid) == 100


def test_validated_delivery_decreases_stock(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "FRN-CHR-01")
    receive(client, auth_headers, pid, 50)

    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "delivery",
            "partner_name": "Acme Offices",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 10}],
        },
    )
    assert created.status_code == 201
    assert created.json()["dest_location"]["type"] == "customer"
    assert created.json()["reference"].startswith("WH1/OUT/")

    client.post(f"/operations/{created.json()['id']}/validate", headers=auth_headers)
    assert on_hand(client, auth_headers, pid) == 40


def test_delivery_beyond_available_stock_is_refused(
    client: TestClient, auth_headers, seeded
) -> None:
    pid = product_id(client, auth_headers, "FRN-CHR-01")
    receive(client, auth_headers, pid, 5)

    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "delivery",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 20}],
        },
    ).json()

    response = client.post(f"/operations/{created['id']}/validate", headers=auth_headers)
    assert response.status_code == 409
    assert "available" in response.json()["detail"]
    # The refusal leaves the stock exactly as it was.
    assert on_hand(client, auth_headers, pid) == 5


def test_internal_transfer_keeps_the_total_and_moves_the_location(
    client: TestClient, auth_headers, seeded
) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    receive(client, auth_headers, pid, 100)

    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "internal",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "dest_location_id": location_id(client, auth_headers, "WH1/PRODUCTION-RACK"),
            "lines": [{"product_id": pid, "qty_demand": 40}],
        },
    ).json()
    assert created["reference"].startswith("WH1/INT/")

    client.post(f"/operations/{created['id']}/validate", headers=auth_headers)

    assert on_hand(client, auth_headers, pid) == 100  # total unchanged

    stock = client.get(f"/products/{pid}/stock", headers=auth_headers).json()
    by_code = {row["location_code"]: Decimal(row["on_hand"]) for row in stock["by_location"]}
    assert by_code == {"WH1/MAIN-STORE": Decimal(60), "WH1/PRODUCTION-RACK": Decimal(40)}


def test_transfer_between_warehouses(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "PKG-BOX-L")
    receive(client, auth_headers, pid, 200)

    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "internal",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "dest_location_id": location_id(client, auth_headers, "WH2/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 80}],
        },
    ).json()
    client.post(f"/operations/{created['id']}/validate", headers=auth_headers)

    stock = client.get(f"/products/{pid}/stock", headers=auth_headers).json()
    by_code = {row["location_code"]: Decimal(row["on_hand"]) for row in stock["by_location"]}
    assert by_code["WH2/MAIN-STORE"] == 80
    assert Decimal(stock["total_on_hand"]) == 200


def test_validating_twice_is_refused(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    document = receive(client, auth_headers, pid, 100)

    again = client.post(f"/operations/{document['id']}/validate", headers=auth_headers)
    assert again.status_code == 409
    # The stock was not added a second time.
    assert on_hand(client, auth_headers, pid) == 100


def test_pick_quantity_overrides_the_requested_quantity(
    client: TestClient, auth_headers, seeded
) -> None:
    pid = product_id(client, auth_headers, "FRN-CHR-01")
    receive(client, auth_headers, pid, 50)

    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "delivery",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 10}],
        },
    ).json()

    # Pick 7 of the 10 asked for, then validate: the ledger records what moved.
    picked = client.patch(
        f"/operations/{created['id']}",
        headers=auth_headers,
        json={"status": "ready", "lines": [{"product_id": pid, "qty_demand": 10, "qty_done": 7}]},
    )
    assert picked.status_code == 200
    assert picked.json()["status"] == "ready"

    client.post(f"/operations/{created['id']}/validate", headers=auth_headers)
    assert on_hand(client, auth_headers, pid) == 43


def test_cancelled_document_cannot_be_validated(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    created = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "receipt",
            "dest_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 100}],
        },
    ).json()

    assert client.post(f"/operations/{created['id']}/cancel", headers=auth_headers).json()[
        "status"
    ] == "canceled"
    assert client.post(f"/operations/{created['id']}/validate", headers=auth_headers).status_code == 409
    assert on_hand(client, auth_headers, pid) == 0


def test_validated_document_cannot_be_cancelled_or_edited(
    client: TestClient, auth_headers, seeded
) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    document = receive(client, auth_headers, pid, 100)

    cancelled = client.post(f"/operations/{document['id']}/cancel", headers=auth_headers)
    assert cancelled.status_code == 409
    assert "adjustment" in cancelled.json()["detail"]

    edited = client.patch(
        f"/operations/{document['id']}", headers=auth_headers, json={"note": "too late"}
    )
    assert edited.status_code == 409


def test_a_document_needs_at_least_one_line(client: TestClient, auth_headers, seeded) -> None:
    response = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "receipt",
            "dest_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [],
        },
    )
    assert response.status_code == 422


def test_transfer_needs_both_ends(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    response = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "internal",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 10}],
        },
    )
    assert response.status_code == 422
    assert "destination" in response.json()["detail"]


def test_source_and_destination_must_differ(client: TestClient, auth_headers, seeded) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    store = location_id(client, auth_headers, "WH1/MAIN-STORE")
    response = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "internal",
            "src_location_id": store,
            "dest_location_id": store,
            "lines": [{"product_id": pid, "qty_demand": 10}],
        },
    )
    assert response.status_code == 422


def test_references_increment_per_warehouse_and_type(
    client: TestClient, auth_headers, seeded
) -> None:
    pid = product_id(client, auth_headers, "STL-ROD-12")
    first = receive(client, auth_headers, pid, 10)
    second = receive(client, auth_headers, pid, 10)

    assert first["reference"] == "WH1/IN/0001"
    assert second["reference"] == "WH1/IN/0002"

    delivery = client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "delivery",
            "src_location_id": location_id(client, auth_headers, "WH1/MAIN-STORE"),
            "lines": [{"product_id": pid, "qty_demand": 5}],
        },
    ).json()
    # Deliveries have their own sequence.
    assert delivery["reference"] == "WH1/OUT/0001"


def test_filters(client: TestClient, auth_headers, seeded) -> None:
    steel = product_id(client, auth_headers, "STL-ROD-12")
    chair = product_id(client, auth_headers, "FRN-CHR-01")
    receive(client, auth_headers, steel, 100)
    client.post(
        "/operations",
        headers=auth_headers,
        json={
            "doc_type": "receipt",
            "partner_name": "Chair Makers Ltd",
            "dest_location_id": location_id(client, auth_headers, "WH2/MAIN-STORE"),
            "lines": [{"product_id": chair, "qty_demand": 20}],
        },
    )

    assert client.get("/operations", headers=auth_headers).json()["total"] == 2
    assert (
        client.get("/operations", headers=auth_headers, params={"status": "done"}).json()["total"]
        == 1
    )
    assert (
        client.get("/operations", headers=auth_headers, params={"status": "draft"}).json()["total"]
        == 1
    )
    assert (
        client.get("/operations", headers=auth_headers, params={"doc_type": "delivery"}).json()[
            "total"
        ]
        == 0
    )

    warehouses = client.get("/warehouses", headers=auth_headers).json()
    wh2 = next(w for w in warehouses if w["code"] == "WH2")
    by_warehouse = client.get(
        "/operations", headers=auth_headers, params={"warehouse_id": wh2["id"]}
    ).json()
    assert by_warehouse["total"] == 1
    assert by_warehouse["items"][0]["partner_name"] == "Chair Makers Ltd"

    by_partner = client.get("/operations", headers=auth_headers, params={"q": "chair"}).json()
    assert by_partner["total"] == 1

    categories = client.get("/categories", headers=auth_headers).json()
    finished = next(c for c in categories if c["name"] == "Finished Goods")
    by_category = client.get(
        "/operations", headers=auth_headers, params={"category_id": finished["id"]}
    ).json()
    assert by_category["total"] == 1


def test_unknown_filter_values_are_rejected(client: TestClient, auth_headers, seeded) -> None:
    assert (
        client.get("/operations", headers=auth_headers, params={"doc_type": "nonsense"}).status_code
        == 422
    )
    assert (
        client.get("/operations", headers=auth_headers, params={"status": "nonsense"}).status_code
        == 422
    )
