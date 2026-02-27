"""Тесты сброса пароля: POST /api/auth/forgot-password, POST /api/auth/reset-password"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password
from tests.conftest import fake_redis


async def test_forgot_password_success(
    client: AsyncClient, test_user: User
):
    """Запрос сброса пароля для верифицированного пользователя → 200, код в Redis."""
    response = await client.post("/api/auth/forgot-password", json={
        "email": "test@utg.uz",
    })
    assert response.status_code == 200

    # Проверяем что код сохранён в Redis
    code = await fake_redis.get("password_reset:test@utg.uz")
    assert code is not None
    assert len(code) == 6


async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Несуществующий email → 404."""
    response = await client.post("/api/auth/forgot-password", json={
        "email": "nobody@utg.uz",
    })
    assert response.status_code == 404


async def test_forgot_password_unverified_user(
    client: AsyncClient, db_session: AsyncSession
):
    """Неверифицированный пользователь → 400."""
    user = User(
        id=uuid.uuid4(),
        email="unverified@utg.uz",
        hashed_password=hash_password("pass123"),
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/forgot-password", json={
        "email": "unverified@utg.uz",
    })
    assert response.status_code == 400


async def test_forgot_password_rate_limit(
    client: AsyncClient, test_user: User
):
    """Повторный запрос сброса менее чем через минуту → 429."""
    # Сохраняем код с большим TTL (как будто только что отправили)
    await fake_redis.setex("password_reset:test@utg.uz", 590, "123456")

    response = await client.post("/api/auth/forgot-password", json={
        "email": "test@utg.uz",
    })
    assert response.status_code == 429


async def test_reset_password_success(
    client: AsyncClient, test_user: User
):
    """Успешный сброс пароля → можно логиниться с новым паролем."""
    # Сохраняем код сброса
    await fake_redis.setex("password_reset:test@utg.uz", 600, "654321")

    response = await client.post("/api/auth/reset-password", json={
        "email": "test@utg.uz",
        "code": "654321",
        "new_password": "newpassword123",
    })
    assert response.status_code == 200

    # Проверяем что можно логиниться с новым паролем
    login_response = await client.post("/api/auth/login", json={
        "email": "test@utg.uz",
        "password": "newpassword123",
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


async def test_reset_password_wrong_code(
    client: AsyncClient, test_user: User
):
    """Неправильный код сброса → 400."""
    await fake_redis.setex("password_reset:test@utg.uz", 600, "654321")

    response = await client.post("/api/auth/reset-password", json={
        "email": "test@utg.uz",
        "code": "000000",
        "new_password": "newpassword123",
    })
    assert response.status_code == 400


async def test_reset_password_short_password(client: AsyncClient):
    """Слишком короткий новый пароль → 422."""
    response = await client.post("/api/auth/reset-password", json={
        "email": "test@utg.uz",
        "code": "123456",
        "new_password": "ab",
    })
    assert response.status_code == 422
