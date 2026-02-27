"""Тесты регистрации: POST /api/auth/register"""

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password


async def test_register_new_user(client: AsyncClient):
    """Успешная регистрация нового пользователя с @utg.uz."""
    response = await client.post("/api/auth/register", json={
        "email": "newuser@utg.uz",
        "password": "securepass123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    assert "message" in response.json()


async def test_register_non_corporate_email(client: AsyncClient):
    """Регистрация с не-корпоративной почтой должна быть отклонена."""
    response = await client.post("/api/auth/register", json={
        "email": "user@gmail.com",
        "password": "securepass123",
        "full_name": "Hacker",
    })
    assert response.status_code == 422


async def test_register_duplicate_verified_email(
    client: AsyncClient, test_user: User
):
    """Повторная регистрация уже верифицированного email — 409 Conflict."""
    response = await client.post("/api/auth/register", json={
        "email": "test@utg.uz",
        "password": "anotherpass",
        "full_name": "Duplicate",
    })
    assert response.status_code == 409


async def test_register_duplicate_unverified_email(
    client: AsyncClient, db_session: AsyncSession
):
    """Повторная регистрация НЕверифицированного email — обновляет данные и отправляет код."""
    # Создаём неверифицированного пользователя
    user = User(
        id=uuid.uuid4(),
        email="unverified@utg.uz",
        hashed_password=hash_password("oldpass"),
        full_name="Old Name",
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    # Регистрируемся заново с тем же email
    response = await client.post("/api/auth/register", json={
        "email": "unverified@utg.uz",
        "password": "newpass123",
        "full_name": "New Name",
    })
    assert response.status_code == 201


async def test_register_missing_password(client: AsyncClient):
    """Регистрация без пароля — 422 ошибка валидации."""
    response = await client.post("/api/auth/register", json={
        "email": "nopass@utg.uz",
    })
    assert response.status_code == 422
