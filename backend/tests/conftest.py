"""Test fixtures.

Tests never touch the real PostgreSQL database: every test gets a fresh
in-memory SQLite database, injected by overriding the `get_db` dependency.
"""

import os

# Must be set before `app` is imported so the module-level engine never
# points at a real Postgres server.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_product():
    return {
        "sku": "TEST-0001",
        "name": "Barcode Scanner",
        "category": "Electronics",
        "quantity": 20,
        "reorder_level": 5,
        "unit_price": 2499.0,
        "supplier": "ScanCo",
        "location": "A1-09",
    }


@pytest.fixture()
def created_product(client, sample_product):
    response = client.post("/api/products", json=sample_product)
    assert response.status_code == 201
    return response.json()
