"""Тесты верификации email: POST /api/auth/verify-email"""

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password
from tests.conftest import fake_redis


async def _create_unverified_user(db_session: AsyncSession, email: str = "new@utg.uz") -> User:
    """Вспомогательная функция: создаёт неверифицированного пользователя."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("password123"),
        full_name="New User",
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_verify_email_success(
    client: AsyncClient, db_session: AsyncSession
):
    """Правильный код → пользователь становится верифицированным."""
    user = await _create_unverified_user(db_session)

    # Сохраняем код в fakeredis (как это делает store_verification_code)
    await fake_redis.setex(f"verify:{user.email}", 600, "123456")

    response = await client.post("/api/auth/verify-email", json={
        "email": user.email,
        "code": "123456",
    })
    assert response.status_code == 200

    # Проверяем что пользователь теперь верифицирован
    result = await db_session.execute(select(User).where(User.id == user.id))
    updated_user = result.scalar_one()
    assert updated_user.is_verified is True

    # Проверяем что код удалён из Redis (одноразовый)
    stored = await fake_redis.get(f"verify:{user.email}")
    assert stored is None


async def test_verify_email_wrong_code(
    client: AsyncClient, db_session: AsyncSession
):
    """Неправильный код → 400."""
    user = await _create_unverified_user(db_session)
    await fake_redis.setex(f"verify:{user.email}", 600, "123456")

    response = await client.post("/api/auth/verify-email", json={
        "email": user.email,
        "code": "000000",
    })
    assert response.status_code == 400


async def test_verify_email_expired_code(
    client: AsyncClient, db_session: AsyncSession
):
    """Нет кода в Redis (истёк) → 400."""
    user = await _create_unverified_user(db_session)
    # Не сохраняем код — он как бы истёк

    response = await client.post("/api/auth/verify-email", json={
        "email": user.email,
        "code": "123456",
    })
    assert response.status_code == 400


async def test_verify_email_already_verified(
    client: AsyncClient, test_user: User
):
    """Уже верифицированный пользователь → 400."""
    response = await client.post("/api/auth/verify-email", json={
        "email": "test@utg.uz",
        "code": "123456",
    })
    assert response.status_code == 400


async def test_verify_email_user_not_found(client: AsyncClient):
    """Несуществующий email → 404."""
    response = await client.post("/api/auth/verify-email", json={
        "email": "nobody@utg.uz",
        "code": "123456",
    })
    assert response.status_code == 404


async def test_verify_email_invalid_code_format(client: AsyncClient):
    """Некорректный формат кода (не 6 цифр) → 422."""
    response = await client.post("/api/auth/verify-email", json={
        "email": "test@utg.uz",
        "code": "abc",
    })
    assert response.status_code == 422
