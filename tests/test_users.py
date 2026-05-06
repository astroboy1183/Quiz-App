"""Integration tests for /users router using TestClient + in-memory SQLite."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.database import Base, get_db
from backend.main import app
from backend.models import Answer, QuizSession, User  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "secret123",
}


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _register_and_login(client: AsyncClient) -> str:
    """Helper: register a user and return the access token."""
    resp = await client.post("/users/register", json=_REGISTER_PAYLOAD)
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/users/register", json=_REGISTER_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/users/register", json=_REGISTER_PAYLOAD)
    resp = await client.post("/users/register", json=_REGISTER_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await _register_and_login(client)
    resp = await client.post(
        "/users/login",
        json={
            "email": _REGISTER_PAYLOAD["email"],
            "password": _REGISTER_PAYLOAD["password"],
        },
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await _register_and_login(client)
    resp = await client.post(
        "/users/login",
        json={"email": _REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    me = resp.json()
    assert me["email"] == _REGISTER_PAYLOAD["email"]
    assert me["username"] == _REGISTER_PAYLOAD["username"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.put(
        "/users/me/settings",
        json={
            "preferred_topic": "History",
            "preferred_difficulty": "Hard",
            "question_count": 15,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["preferred_topic"] == "History"
    assert data["preferred_difficulty"] == "Hard"
    assert data["question_count"] == 15


@pytest.mark.asyncio
async def test_history_empty(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get(
        "/users/me/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
