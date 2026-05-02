import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.answer_evaluator import evaluate_answer
from backend.agents.orchestrator import orchestrator
from backend.agents.question_generator import generate_questions
from backend.database import get_db
from backend.schemas.quiz import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    Question,
    QuizResultsResponse,
    QuizStartRequest,
    QuizStartResponse,
)
from backend.services.quiz_service import (
    create_session,
    finalise_session,
    record_answer,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])

# In-memory question cache: session_id → list of RawQuestion
# Replaced by Redis in Sprint 6 for multiplayer support
_question_cache: dict[str, list] = {}


@router.post("/start", response_model=QuizStartResponse, status_code=201)
async def start_quiz(body: QuizStartRequest, db: AsyncSession = Depends(get_db)):
    session = await create_session(
        db,
        topic=body.topic,
        difficulty=body.difficulty,
        total_qs=body.total_qs,
    )

    # Pre-generate all questions and cache them for this session
    questions = await generate_questions(body.topic, body.difficulty, body.total_qs)
    _question_cache[str(session.id)] = questions

    await orchestrator.on_session_start(session.id, body.topic, body.difficulty)

    return QuizStartResponse(
        session_id=session.id,
        topic=session.topic,
        difficulty=session.difficulty,
        total_qs=session.total_qs,
        created_at=session.created_at or datetime.utcnow(),
    )


@router.get("/{session_id}/question/{n}", response_model=Question)
async def get_question(session_id: uuid.UUID, n: int):
    questions = _question_cache.get(str(session_id))
    if not questions:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    if n < 1 or n > len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Question number must be between 1 and {len(questions)}",
        )

    q = questions[n - 1]
    return Question(
        question_number=n,
        question_text=q.question_text,
        options=q.options,
        topic=q.topic,
        difficulty=q.difficulty,
    )


@router.post("/{session_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: uuid.UUID,
    body: AnswerSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    questions = _question_cache.get(str(session_id))
    if not questions:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    is_correct = evaluate_answer(body.selected_option, body.correct_answer)

    await record_answer(
        db,
        session_id=session_id,
        question_text=body.question_text,
        correct_answer=body.correct_answer,
        user_answer=body.selected_option,
        is_correct=is_correct,
        topic=body.topic,
        difficulty=body.difficulty,
        time_taken=body.time_taken,
    )

    await orchestrator.on_answer_submitted(session_id, body.question_number, is_correct)

    return AnswerSubmitResponse(
        is_correct=is_correct, correct_answer=body.correct_answer
    )


@router.get("/{session_id}/results", response_model=QuizResultsResponse)
async def get_results(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        results = await finalise_session(db, session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    await orchestrator.on_session_end(session_id, results.score, results.accuracy)

    # Clean up question cache after session ends
    _question_cache.pop(str(session_id), None)

    return results
