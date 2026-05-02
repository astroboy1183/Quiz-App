"""Integration tests for /quiz router using TestClient + in-memory SQLite."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.database import Base, get_db
from backend.main import app
from backend.models import Answer, QuizSession  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

MOCK_QUESTIONS = [
    {
        "question_text": f"Question {i}?",
        "options": {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
        "correct_answer": "A",
        "topic": "Science",
        "difficulty": "Easy",
    }
    for i in range(1, 11)
]


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

    from backend.agents.question_generator import RawQuestion

    mock_questions = [RawQuestion(**q) for q in MOCK_QUESTIONS]

    with patch(
        "backend.routers.quiz.generate_questions",
        new=AsyncMock(return_value=mock_questions),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_start_quiz(client: AsyncClient):
    resp = await client.post(
        "/quiz/start", json={"topic": "Science", "difficulty": "Easy", "total_qs": 10}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["topic"] == "Science"
    assert data["total_qs"] == 10


@pytest.mark.asyncio
async def test_get_question(client: AsyncClient):
    start = await client.post(
        "/quiz/start", json={"topic": "Science", "difficulty": "Easy", "total_qs": 10}
    )
    session_id = start.json()["session_id"]

    resp = await client.get(f"/quiz/{session_id}/question/1")
    assert resp.status_code == 200
    q = resp.json()
    assert q["question_number"] == 1
    assert set(q["options"].keys()) == {"A", "B", "C", "D"}


@pytest.mark.asyncio
async def test_submit_answer_correct(client: AsyncClient):
    start = await client.post(
        "/quiz/start", json={"topic": "Science", "difficulty": "Easy", "total_qs": 10}
    )
    session_id = start.json()["session_id"]
    q = (await client.get(f"/quiz/{session_id}/question/1")).json()

    resp = await client.post(
        f"/quiz/{session_id}/answer",
        json={
            "question_number": 1,
            "question_text": q["question_text"],
            "selected_option": "A",
            "correct_answer": "A",
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "time_taken": 10,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True


@pytest.mark.asyncio
async def test_full_quiz_flow(client: AsyncClient):
    start = await client.post(
        "/quiz/start", json={"topic": "Science", "difficulty": "Easy", "total_qs": 10}
    )
    session_id = start.json()["session_id"]

    for i in range(1, 11):
        q = (await client.get(f"/quiz/{session_id}/question/{i}")).json()
        await client.post(
            f"/quiz/{session_id}/answer",
            json={
                "question_number": i,
                "question_text": q["question_text"],
                "selected_option": "A",
                "correct_answer": "A",
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "time_taken": 8,
            },
        )

    resp = await client.get(f"/quiz/{session_id}/results")
    assert resp.status_code == 200
    results = resp.json()
    assert results["score"] == 10
    assert abs(results["accuracy"] - 1.0) < 0.001
