"""Tests for quiz_service logic using an in-memory SQLite DB."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database import Base
from backend.models import Answer, QuizSession  # noqa: F401 — needed for metadata
from backend.services.quiz_service import (
    create_session,
    finalise_session,
    record_answer,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_session(db: AsyncSession):
    session = await create_session(db, topic="Science", difficulty="Easy", total_qs=10)
    assert session.id is not None
    assert session.topic == "Science"
    assert session.difficulty == "Easy"
    assert session.total_qs == 10
    assert session.score == 0


@pytest.mark.asyncio
async def test_record_answer(db: AsyncSession):
    session = await create_session(db, topic="History", difficulty="Medium", total_qs=5)
    answer = await record_answer(
        db,
        session_id=session.id,
        question_text="Who was the first US president?",
        correct_answer="A",
        user_answer="A",
        is_correct=True,
        topic="History",
        difficulty="Medium",
        time_taken=12,
    )
    assert answer.is_correct is True
    assert answer.time_taken == 12


@pytest.mark.asyncio
async def test_finalise_session(db: AsyncSession):
    session = await create_session(db, topic="Science", difficulty="Hard", total_qs=3)

    answers = [
        ("Q1?", "A", "A", True, 10),
        ("Q2?", "B", "A", False, 15),
        ("Q3?", "C", "C", True, 8),
    ]
    for q_text, correct, user, correct_bool, t in answers:
        await record_answer(
            db,
            session_id=session.id,
            question_text=q_text,
            correct_answer=correct,
            user_answer=user,
            is_correct=correct_bool,
            topic="Science",
            difficulty="Hard",
            time_taken=t,
        )

    results = await finalise_session(db, session.id)

    assert results.score == 2
    assert results.total_qs == 3
    assert abs(results.accuracy - 2 / 3) < 0.001
    assert results.time_taken == 33
    assert len(results.topic_breakdown) == 1
    assert results.topic_breakdown[0].topic == "Science"
