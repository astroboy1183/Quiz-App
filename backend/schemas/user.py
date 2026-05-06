import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    preferred_topic: str
    preferred_difficulty: str
    question_count: int
    timer_duration: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    preferred_topic: str | None = None
    preferred_difficulty: str | None = None
    question_count: int | None = Field(default=None, ge=1, le=20)
    timer_duration: int | None = Field(default=None, ge=10, le=120)


class QuizHistoryItem(BaseModel):
    session_id: uuid.UUID
    topic: str
    difficulty: str
    score: int
    total_qs: int
    accuracy: float
    time_taken: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class QuizHistoryResponse(BaseModel):
    items: list[QuizHistoryItem]
    total: int
    page: int
    page_size: int
