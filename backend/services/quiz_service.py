import uuid
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.answer import Answer
from backend.models.session import QuizSession
from backend.schemas.quiz import QuizResultsResponse, TopicBreakdown


async def create_session(
    db: AsyncSession,
    topic: str,
    difficulty: str,
    total_qs: int,
    user_id: uuid.UUID | None = None,
) -> QuizSession:
    session = QuizSession(
        topic=topic,
        difficulty=difficulty,
        total_qs=total_qs,
        user_id=user_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def record_answer(
    db: AsyncSession,
    session_id: uuid.UUID,
    question_text: str,
    correct_answer: str,
    user_answer: str | None,
    is_correct: bool,
    topic: str,
    difficulty: str,
    time_taken: int,
) -> Answer:
    answer = Answer(
        session_id=session_id,
        question_text=question_text,
        correct_answer=correct_answer,
        user_answer=user_answer,
        is_correct=is_correct,
        topic=topic,
        difficulty=difficulty,
        time_taken=time_taken,
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer


async def finalise_session(
    db: AsyncSession, session_id: uuid.UUID
) -> QuizResultsResponse:
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one()

    answers_result = await db.execute(
        select(Answer).where(Answer.session_id == session_id)
    )
    answers = answers_result.scalars().all()

    correct_count = sum(1 for a in answers if a.is_correct)
    total_time = sum(a.time_taken or 0 for a in answers)
    accuracy = correct_count / len(answers) if answers else 0.0

    # per-topic breakdown
    topic_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for a in answers:
        topic_stats[a.topic]["total"] += 1
        if a.is_correct:
            topic_stats[a.topic]["correct"] += 1

    breakdown = [
        TopicBreakdown(
            topic=t,
            correct=v["correct"],
            total=v["total"],
            accuracy=v["correct"] / v["total"] if v["total"] else 0.0,
        )
        for t, v in topic_stats.items()
    ]

    await db.execute(
        update(QuizSession)
        .where(QuizSession.id == session_id)
        .values(score=correct_count, accuracy=accuracy, time_taken=total_time)
    )
    await db.commit()

    return QuizResultsResponse(
        session_id=session_id,
        topic=session.topic,
        difficulty=session.difficulty,
        score=correct_count,
        total_qs=session.total_qs,
        accuracy=accuracy,
        time_taken=total_time,
        topic_breakdown=breakdown,
    )
