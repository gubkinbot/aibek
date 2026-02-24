"""Роутер аутентификации: регистрация, вход, верификация email, сброс пароля."""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_user_permissions
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

_MESSAGES = {
    "ru": {
        "code_sent": "Код подтверждения отправлен на вашу почту",
        "code_resent": "Код подтверждения повторно отправлен на вашу почту",
        "code_resent_again": "Код подтверждения отправлен повторно",
        "email_already_registered": "Этот email уже зарегистрирован",
        "user_not_found": "Пользователь не найден",
        "email_already_verified": "Email уже подтверждён",
        "invalid_code": "Неверный или истёкший код подтверждения",
        "email_verified": "Email успешно подтверждён",
        "wait_before_resend": "Подождите минуту перед повторной отправкой кода",
        "invalid_credentials": "Неверные учётные данные",
        "email_not_verified": "Email не подтверждён. Проверьте вашу почту.",
        "account_deactivated": "Аккаунт деактивирован",
        "email_not_registered": "Этот email не зарегистрирован",
        "reset_code_sent": "Код сброса пароля отправлен на вашу почту",
        "invalid_reset_code": "Неверный или истёкший код",
        "password_changed": "Пароль успешно изменён",
        "email_send_error": "Ошибка отправки письма. Попробуйте позже.",
    },
    "uz": {
        "code_sent": "Tasdiqlash kodi pochtangizga yuborildi",
        "code_resent": "Tasdiqlash kodi qayta yuborildi",
        "code_resent_again": "Tasdiqlash kodi qayta yuborildi",
        "email_already_registered": "Bu email allaqachon ro'yxatdan o'tgan",
        "user_not_found": "Foydalanuvchi topilmadi",
        "email_already_verified": "Email allaqachon tasdiqlangan",
        "invalid_code": "Noto'g'ri yoki muddati o'tgan tasdiqlash kodi",
        "email_verified": "Email muvaffaqiyatli tasdiqlandi",
        "wait_before_resend": "Kodni qayta yuborishdan oldin bir daqiqa kuting",
        "invalid_credentials": "Noto'g'ri hisob ma'lumotlari",
        "email_not_verified": "Email tasdiqlanmagan. Pochtangizni tekshiring.",
        "account_deactivated": "Hisob o'chirilgan",
        "email_not_registered": "Bu email ro'yxatdan o'tmagan",
        "reset_code_sent": "Parolni tiklash kodi pochtangizga yuborildi",
        "invalid_reset_code": "Noto'g'ri yoki muddati o'tgan kod",
        "password_changed": "Parol muvaffaqiyatli o'zgartirildi",
        "email_send_error": "Xat yuborishda xatolik. Keyinroq urinib ko'ring.",
    },
}


def _msg(lang: str, key: str) -> str:
    """Возвращает локализованное сообщение по ключу и языку."""
    lang = (lang or "ru").strip().lower()[:2]
    return _MESSAGES.get(lang, _MESSAGES["ru"])[key]


async def _send_code(email: str, lang: str = "ru") -> None:
    """Генерирует код подтверждения и отправляет его на email."""
    code = generate_verification_code()
    await store_verification_code(email, code)
    try:
        await send_verification_email(email, code, lang=lang)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_msg(lang, "email_send_error"),
        )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Регистрация нового пользователя с корпоративной почтой @utg.uz."""
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_msg(accept_language, "email_already_registered"),
            )
        # Not verified — update and resend code
        existing_user.hashed_password = hash_password(data.password)
        existing_user.full_name = data.full_name
        await db.commit()
        await _send_code(data.email, lang=accept_language)
        return MessageResponse(message=_msg(accept_language, "code_resent"))

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()

    await _send_code(data.email, lang=accept_language)
    return MessageResponse(message=_msg(accept_language, "code_sent"))


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Подтверждение email по 6-значному коду."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_msg(accept_language, "user_not_found"),
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "email_already_verified"),
        )

    is_valid = await verify_code(data.email, data.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "invalid_code"),
        )

    user.is_verified = True

    # Auto-set superadmin flag if email matches SUPERADMIN_EMAIL
    from app.config import settings
    if settings.superadmin_email and data.email.lower() == settings.superadmin_email.lower():
        if not user.is_superadmin:
            user.is_superadmin = True
            logger.info("Auto-set superadmin flag for %s", data.email)

    await db.commit()

    # Назначить доступ по умолчанию (если пользователь не суперадмин)
    if not user.is_superadmin:
        from app.services.module_access import apply_default_access
        await apply_default_access(user.id, db)

    return MessageResponse(message=_msg(accept_language, "email_verified"))


@router.post("/resend-code", response_model=MessageResponse)
async def resend_code(
    data: ResendCodeRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Повторная отправка кода подтверждения email."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_msg(accept_language, "user_not_found"),
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "email_already_verified"),
        )

    if await has_recent_code(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_msg(accept_language, "wait_before_resend"),
        )

    await _send_code(data.email, lang=accept_language)
    return MessageResponse(message=_msg(accept_language, "code_resent_again"))


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Вход в систему: проверка email/пароля, выдача JWT-токена."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_msg(accept_language, "invalid_credentials"),
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": _msg(accept_language, "email_not_verified"),
                "code": "email_not_verified",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_msg(accept_language, "account_deactivated"),
        )

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


PASSWORD_RESET_PREFIX = "password_reset"


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Запрос сброса пароля: отправка кода на email."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_msg(accept_language, "email_not_registered"),
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "email_not_verified"),
        )

    if await has_recent_code(data.email, prefix=PASSWORD_RESET_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_msg(accept_language, "wait_before_resend"),
        )

    code = generate_verification_code()
    await store_verification_code(data.email, code, prefix=PASSWORD_RESET_PREFIX)
    try:
        await send_password_reset_email(data.email, code, lang=accept_language)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_msg(accept_language, "email_send_error"),
        )

    return MessageResponse(message=_msg(accept_language, "reset_code_sent"))


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: str = Header("ru"),
):
    """Сброс пароля по коду подтверждения."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "invalid_reset_code"),
        )

    is_valid = await verify_code(data.email, data.code, prefix=PASSWORD_RESET_PREFIX)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(accept_language, "invalid_reset_code"),
        )

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return MessageResponse(message=_msg(accept_language, "password_changed"))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_active_user)):
    """Получение данных текущего пользователя (профиль, permissions, уровни доступа)."""
    permissions = ["*"] if user.is_superadmin else get_user_permissions(user)
    module_access = {ma.module: ma.level for ma in user.module_access}
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        auth_provider=user.auth_provider,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_superadmin=user.is_superadmin,
        permissions=permissions,
        module_access=module_access,
        created_at=user.created_at,
    )
