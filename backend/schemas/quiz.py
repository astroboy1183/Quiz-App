import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TOPICS = Literal[
    "Science",
    "History",
    "Geography",
    "Sports",
    "Technology",
    "Arts",
    "Politics",
    "Pop Culture",
    "Mathematics",
    "Mixed",
]
DIFFICULTIES = Literal["Easy", "Medium", "Hard"]


# ── Session ──────────────────────────────────────────────────────────────────


class QuizStartRequest(BaseModel):
    topic: TOPICS = "Mixed"
    difficulty: DIFFICULTIES = "Medium"
    total_qs: int = Field(default=10, ge=1, le=20)


class QuizStartResponse(BaseModel):
    session_id: uuid.UUID
    topic: str
    difficulty: str
    total_qs: int
    created_at: datetime


# ── Question ─────────────────────────────────────────────────────────────────


class Question(BaseModel):
    question_number: int
    question_text: str
    options: dict[str, str]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    topic: str
    difficulty: str


# ── Answer submission ─────────────────────────────────────────────────────────


class AnswerSubmitRequest(BaseModel):
    question_number: int
    question_text: str
    selected_option: str | None = None  # None = timed out
    topic: str
    difficulty: str
    time_taken: int = Field(default=0, ge=0)


class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None = None


# ── Results ───────────────────────────────────────────────────────────────────


class TopicBreakdown(BaseModel):
    topic: str
    correct: int
    total: int
    accuracy: float


class QuizResultsResponse(BaseModel):
    session_id: uuid.UUID
    topic: str
    difficulty: str
    score: int
    total_qs: int
    accuracy: float
    time_taken: int
    topic_breakdown: list[TopicBreakdown]
