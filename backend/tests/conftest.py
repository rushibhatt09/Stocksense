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
