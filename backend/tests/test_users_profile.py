"""Тесты профиля пользователя: GET /api/auth/me, PATCH /api/users/me, POST /api/users/me/change-password"""

from httpx import AsyncClient

from app.models.user import User


async def test_get_me_authenticated(
    client: AsyncClient, test_user: User, auth_headers: dict
):
    """GET /api/auth/me с валидным токеном → данные пользователя."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@utg.uz"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert data["is_verified"] is True
    assert data["is_superadmin"] is False


async def test_get_me_no_token(client: AsyncClient):
    """GET /api/auth/me без токена → 403."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 403


async def test_get_me_invalid_token(client: AsyncClient):
    """GET /api/auth/me с невалидным токеном → 401."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


async def test_update_profile(
    client: AsyncClient, test_user: User, auth_headers: dict
):
    """PATCH /api/users/me — обновление имени."""
    response = await client.patch(
        "/api/users/me",
        json={"full_name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


async def test_change_password_success(
    client: AsyncClient, test_user: User, auth_headers: dict
):
    """Смена пароля с правильным текущим паролем → 200."""
    response = await client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Проверяем что можно логиниться с новым паролем
    login_response = await client.post("/api/auth/login", json={
        "email": "test@utg.uz",
        "password": "newpassword456",
    })
    assert login_response.status_code == 200


async def test_change_password_wrong_current(
    client: AsyncClient, test_user: User, auth_headers: dict
):
    """Смена пароля с неправильным текущим паролем → 400."""
    response = await client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
