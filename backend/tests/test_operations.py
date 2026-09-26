from fastapi.testclient import TestClient


def _line(product_id: int, qty: float) -> dict:
    return {"product_id": product_id, "qty": qty}


def _headers_of(client: TestClient, setup: dict) -> dict[str, str]:
    """warehouse_setup was built via the manager account; log back in for headers."""
    token = client.post(
        "/auth/login", json={"email": "manager@example.com", "password": "supersecret1"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _receive(client: TestClient, headers: dict[str, str], setup: dict, qty: float) -> None:
    receipt = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], qty)],
        },
        headers=headers,
    ).json()
    assert client.post(f"/documents/{receipt['id']}/validate", headers=headers).status_code == 200


def test_receipt_increases_stock(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)

    receipt = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "partner_name": "Steel Corp",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 100)],
        },
        headers=headers,
    )
    assert receipt.status_code == 201, receipt.text
    doc = receipt.json()
    assert doc["status"] == "draft"
    assert doc["reference"].startswith("WH1/IN/")

    validated = client.post(f"/documents/{doc['id']}/validate", headers=headers)
    assert validated.status_code == 200, validated.text
    assert validated.json()["status"] == "done"
    assert validated.json()["lines"][0]["qty_done"] == 100

    product = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert product["on_hand"] == 100


def test_delivery_decreases_stock(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 100)

    delivery = client.post(
        "/documents",
        json={
            "doc_type": "delivery",
            "partner_name": "ABC Inc",
            "src_location_id": setup["main_store"]["id"],
            "dest_location_id": setup["customers"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    ).json()

    validated = client.post(f"/documents/{delivery['id']}/validate", headers=headers)
    assert validated.status_code == 200, validated.text

    product = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert product["on_hand"] == 90


def test_delivery_rejects_insufficient_stock(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 5)

    delivery = client.post(
        "/documents",
        json={
            "doc_type": "delivery",
            "src_location_id": setup["main_store"]["id"],
            "dest_location_id": setup["customers"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    ).json()

    response = client.post(f"/documents/{delivery['id']}/validate", headers=headers)
    assert response.status_code == 400
    assert "Not enough stock" in response.json()["detail"]

    # Stock must be unchanged, and the document must not have been marked done.
    product = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert product["on_hand"] == 5
    doc = client.get(f"/documents/{delivery['id']}", headers=headers).json()
    assert doc["status"] == "draft"


def test_internal_transfer_moves_location_not_total(
    client: TestClient, warehouse_setup: dict
) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 100)

    transfer = client.post(
        "/documents",
        json={
            "doc_type": "internal",
            "src_location_id": setup["main_store"]["id"],
            "dest_location_id": setup["rack_b"]["id"],
            "lines": [_line(setup["product"]["id"], 40)],
        },
        headers=headers,
    ).json()
    assert client.post(f"/documents/{transfer['id']}/validate", headers=headers).status_code == 200

    total = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert total["on_hand"] == 100  # unchanged company-wide

    by_location = client.get(
        f"/products/{setup['product']['id']}/stock", headers=headers
    ).json()
    balances = {row["location"]["id"]: row["on_hand"] for row in by_location}
    assert balances[setup["main_store"]["id"]] == 60
    assert balances[setup["rack_b"]["id"]] == 40


def test_internal_transfer_rejects_same_location(
    client: TestClient, warehouse_setup: dict
) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    response = client.post(
        "/documents",
        json={
            "doc_type": "internal",
            "src_location_id": setup["main_store"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 1)],
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_adjustment_decreases_for_damage(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 20)

    adjustment = client.post(
        "/documents",
        json={
            "doc_type": "adjustment",
            "src_location_id": setup["adjustment"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "note": "3 kg damaged in storage",
            "lines": [_line(setup["product"]["id"], 17)],  # counted 17 of a recorded 20
        },
        headers=headers,
    ).json()

    validated = client.post(f"/documents/{adjustment['id']}/validate", headers=headers)
    assert validated.status_code == 200, validated.text
    assert validated.json()["lines"][0]["qty_done"] == 3

    product = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert product["on_hand"] == 17


def test_adjustment_increases_for_found_stock(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 20)

    adjustment = client.post(
        "/documents",
        json={
            "doc_type": "adjustment",
            "src_location_id": setup["adjustment"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 25)],  # counted 25 of a recorded 20
        },
        headers=headers,
    ).json()

    client.post(f"/documents/{adjustment['id']}/validate", headers=headers)
    product = client.get(f"/products/{setup['product']['id']}", headers=headers).json()
    assert product["on_hand"] == 25


def test_adjustment_matching_count_creates_no_move(
    client: TestClient, warehouse_setup: dict
) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 20)

    adjustment = client.post(
        "/documents",
        json={
            "doc_type": "adjustment",
            "src_location_id": setup["adjustment"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 20)],
        },
        headers=headers,
    ).json()
    validated = client.post(f"/documents/{adjustment['id']}/validate", headers=headers).json()
    assert validated["lines"][0]["qty_done"] == 0

    moves = client.get(
        f"/stock-moves?document_id={adjustment['id']}", headers=headers
    ).json()
    assert moves == []


def test_receipt_location_types_enforced(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    # Receipt with a physical source instead of Vendor should fail validation.
    response = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["main_store"]["id"],
            "dest_location_id": setup["rack_b"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_cannot_validate_twice(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    receipt = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    ).json()
    assert client.post(f"/documents/{receipt['id']}/validate", headers=headers).status_code == 200
    second = client.post(f"/documents/{receipt['id']}/validate", headers=headers)
    assert second.status_code == 400


def test_cancel_and_delete_rules(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    receipt = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    ).json()

    # Draft documents can be deleted outright.
    assert client.delete(f"/documents/{receipt['id']}", headers=headers).status_code == 204
    assert client.get(f"/documents/{receipt['id']}", headers=headers).status_code == 404

    receipt2 = client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    ).json()
    client.post(f"/documents/{receipt2['id']}/validate", headers=headers)
    # A validated document cannot be canceled or deleted.
    assert client.post(f"/documents/{receipt2['id']}/cancel", headers=headers).status_code == 400
    assert client.delete(f"/documents/{receipt2['id']}", headers=headers).status_code == 400


def test_dashboard_summary_reflects_pending_and_stock(
    client: TestClient, warehouse_setup: dict
) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)

    client.post(
        "/documents",
        json={
            "doc_type": "receipt",
            "src_location_id": setup["vendors"]["id"],
            "dest_location_id": setup["main_store"]["id"],
            "lines": [_line(setup["product"]["id"], 10)],
        },
        headers=headers,
    )

    summary = client.get("/dashboard/summary", headers=headers).json()
    assert summary["pending_receipts"] == 1
    assert summary["pending_deliveries"] == 0
    assert summary["out_of_stock_count"] == 1  # nothing validated yet


def test_stock_moves_filter_by_product(client: TestClient, warehouse_setup: dict) -> None:
    setup = warehouse_setup
    headers = _headers_of(client, setup)
    _receive(client, headers, setup, 10)

    moves = client.get(
        f"/stock-moves?product_id={setup['product']['id']}", headers=headers
    ).json()
    assert len(moves) == 1
    assert moves[0]["qty"] == 10
    assert moves[0]["to_location"]["id"] == setup["main_store"]["id"]
