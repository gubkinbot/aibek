# Аутентификация

API использует **JWT (JSON Web Token)** для аутентификации пользователей.

## Регистрация

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Иван Иванов"
}
```

**Ответ (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "created_at": "2026-02-17T09:30:00Z"
}
```

## Вход

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Ответ (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

## Использование токена

Передавайте токен в заголовке `Authorization`:

```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Ответ (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "created_at": "2026-02-17T09:30:00Z"
}
```

## Ошибки

| Код | Описание |
|-----|----------|
| `401` | Невалидный или истёкший токен |
| `409` | Email уже зарегистрирован |
