"""Тесты логина: POST /api/auth/login"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password


async def test_login_success(client: AsyncClient, test_user: User):
    """Успешный логин с правильным email и паролем."""
    response = await client.post("/api/auth/login", json={
        "email": "test@utg.uz",
        "password": "testpassword123",
    })
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Неправильный пароль — 401."""
    response = await client.post("/api/auth/login", json={
        "email": "test@utg.uz",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    """Несуществующий email — 401."""
    response = await client.post("/api/auth/login", json={
        "email": "noone@utg.uz",
        "password": "anypassword",
    })
    assert response.status_code == 401


async def test_login_unverified_user(
    client: AsyncClient, db_session: AsyncSession
):
    """Неверифицированный пользователь — 403 с кодом email_not_verified."""
    user = User(
        id=uuid.uuid4(),
        email="unverified@utg.uz",
        hashed_password=hash_password("password123"),
        full_name="Unverified",
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/login", json={
        "email": "unverified@utg.uz",
        "password": "password123",
    })
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "email_not_verified"


async def test_login_blocked_user(
    client: AsyncClient, db_session: AsyncSession
):
    """Заблокированный пользователь — 403."""
    user = User(
        id=uuid.uuid4(),
        email="blocked@utg.uz",
        hashed_password=hash_password("password123"),
        full_name="Blocked",
        is_verified=True,
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/login", json={
        "email": "blocked@utg.uz",
        "password": "password123",
    })
    assert response.status_code == 403
