import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResendCodeRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.email import send_password_reset_email, send_verification_email
from app.services.verification import (
    generate_verification_code,
    has_recent_code,
    store_verification_code,
    verify_code,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _send_code(email: str) -> None:
    code = generate_verification_code()
    await store_verification_code(email, code)
    try:
        await send_verification_email(email, code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки письма. Попробуйте позже.",
        )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот email уже зарегистрирован",
            )
        # Not verified — update and resend code
        existing_user.hashed_password = hash_password(data.password)
        existing_user.full_name = data.full_name
        await db.commit()
        await _send_code(data.email)
        return MessageResponse(message="Код подтверждения повторно отправлен на вашу почту")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()

    await _send_code(data.email)
    return MessageResponse(message="Код подтверждения отправлен на вашу почту")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже подтверждён")

    is_valid = await verify_code(data.email, data.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истёкший код подтверждения",
        )

    user.is_verified = True
    await db.commit()
    return MessageResponse(message="Email успешно подтверждён")


@router.post("/resend-code", response_model=MessageResponse)
async def resend_code(data: ResendCodeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже подтверждён")

    if await has_recent_code(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Подождите минуту перед повторной отправкой кода",
        )

    await _send_code(data.email)
    return MessageResponse(message="Код подтверждения отправлен повторно")


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтверждён. Проверьте вашу почту.",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


PASSWORD_RESET_PREFIX = "password_reset"


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_verified:
        return MessageResponse(message="Если аккаунт существует, код сброса отправлен на вашу почту")

    if await has_recent_code(data.email, prefix=PASSWORD_RESET_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Подождите минуту перед повторной отправкой кода",
        )

    code = generate_verification_code()
    await store_verification_code(data.email, code, prefix=PASSWORD_RESET_PREFIX)
    try:
        await send_password_reset_email(data.email, code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки письма. Попробуйте позже.",
        )

    return MessageResponse(message="Если аккаунт существует, код сброса отправлен на вашу почту")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный или истёкший код")

    is_valid = await verify_code(data.email, data.code, prefix=PASSWORD_RESET_PREFIX)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истёкший код",
        )

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return MessageResponse(message="Пароль успешно изменён")


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
