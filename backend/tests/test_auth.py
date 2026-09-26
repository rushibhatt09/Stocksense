from fastapi.testclient import TestClient


def test_signup_creates_account(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={
            "name": "Inventory Manager",
            "email": "New.Manager@Example.com",
            "password": "supersecret1",
            "role": "manager",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.manager@example.com"  # stored lower case
    assert "password" not in body and "password_hash" not in body


def test_signup_rejects_duplicate_email(client: TestClient, signed_up: dict[str, str]) -> None:
    response = client.post("/auth/signup", json=signed_up)
    assert response.status_code == 409


def test_signup_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={"name": "Short", "email": "short@example.com", "password": "abc", "role": "staff"},
    )
    assert response.status_code == 422


def test_login_returns_token_and_user(client: TestClient, signed_up: dict[str, str]) -> None:
    response = client.post(
        "/auth/login", json={"email": signed_up["email"], "password": signed_up["password"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == signed_up["email"]


def test_login_rejects_wrong_password(client: TestClient, signed_up: dict[str, str]) -> None:
    response = client.post(
        "/auth/login", json={"email": signed_up["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    # The same message for a wrong email, so nothing leaks about who has an account.
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_requires_a_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_me_returns_the_signed_in_user(client: TestClient, signed_up: dict[str, str]) -> None:
    token = client.post(
        "/auth/login", json={"email": signed_up["email"], "password": signed_up["password"]}
    ).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == signed_up["email"]


def test_password_reset_end_to_end(client: TestClient, signed_up: dict[str, str]) -> None:
    forgot = client.post("/auth/forgot-password", json={"email": signed_up["email"]})
    assert forgot.status_code == 200
    otp = forgot.json()["otp"]
    assert otp and len(otp) == 6

    verified = client.post(
        "/auth/verify-otp", json={"email": signed_up["email"], "otp": otp}
    )
    assert verified.status_code == 200
    reset_token = verified.json()["reset_token"]

    reset = client.post(
        "/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "brandnewpass1"},
    )
    assert reset.status_code == 200

    # The new password works and the old one does not.
    assert (
        client.post(
            "/auth/login", json={"email": signed_up["email"], "password": "brandnewpass1"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/auth/login", json={"email": signed_up["email"], "password": signed_up["password"]}
        ).status_code
        == 401
    )


def test_otp_works_only_once(client: TestClient, signed_up: dict[str, str]) -> None:
    otp = client.post("/auth/forgot-password", json={"email": signed_up["email"]}).json()["otp"]
    first = client.post("/auth/verify-otp", json={"email": signed_up["email"], "otp": otp})
    assert first.status_code == 200

    second = client.post("/auth/verify-otp", json={"email": signed_up["email"], "otp": otp})
    assert second.status_code == 400


def test_requesting_a_new_otp_invalidates_the_previous_one(
    client: TestClient, signed_up: dict[str, str]
) -> None:
    first_otp = client.post(
        "/auth/forgot-password", json={"email": signed_up["email"]}
    ).json()["otp"]
    second_otp = client.post(
        "/auth/forgot-password", json={"email": signed_up["email"]}
    ).json()["otp"]

    assert (
        client.post(
            "/auth/verify-otp", json={"email": signed_up["email"], "otp": first_otp}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/auth/verify-otp", json={"email": signed_up["email"], "otp": second_otp}
        ).status_code
        == 200
    )


def test_wrong_otp_is_rejected(client: TestClient, signed_up: dict[str, str]) -> None:
    otp = client.post("/auth/forgot-password", json={"email": signed_up["email"]}).json()["otp"]
    wrong = "000000" if otp != "000000" else "111111"
    response = client.post("/auth/verify-otp", json={"email": signed_up["email"], "otp": wrong})
    assert response.status_code == 400


def test_forgot_password_does_not_reveal_unknown_emails(client: TestClient) -> None:
    response = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert response.json()["otp"] is None


def test_reset_password_rejects_a_forged_token(client: TestClient) -> None:
    response = client.post(
        "/auth/reset-password",
        json={"reset_token": "not-a-real-token", "new_password": "whatever12"},
    )
    assert response.status_code == 400


def test_access_token_is_not_accepted_as_a_reset_token(
    client: TestClient, signed_up: dict[str, str]
) -> None:
    access_token = client.post(
        "/auth/login", json={"email": signed_up["email"], "password": signed_up["password"]}
    ).json()["access_token"]

    response = client.post(
        "/auth/reset-password",
        json={"reset_token": access_token, "new_password": "brandnewpass1"},
    )
    assert response.status_code == 400
