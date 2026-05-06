from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import create_access_token, get_current_user
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import (
    QuizHistoryItem,
    QuizHistoryResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserSettingsUpdate,
)
from backend.services.user_service import (
    authenticate_user,
    create_user,
    get_user_history,
    update_user_settings,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, body.email, body.username, body.password)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/settings", response_model=UserResponse)
async def update_settings(
    body: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_user_settings(db, current_user, body)


@router.get("/me/history", response_model=QuizHistoryResponse)
async def get_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions, total = await get_user_history(db, current_user.id, page, page_size)
    items = [QuizHistoryItem.model_validate(s) for s in sessions]
    return QuizHistoryResponse(items=items, total=total, page=page, page_size=page_size)
