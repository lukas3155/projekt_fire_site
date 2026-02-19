import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Session-scoped test client to avoid asyncpg event loop issues."""
    with TestClient(app) as c:
        yield c
