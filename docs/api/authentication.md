# Аутентификация

API использует **JWT (JSON Web Token)** для аутентификации. Полный цикл: регистрация → подтверждение email → вход → работа с токеном.

## Общая схема

```
1. Регистрация       POST /api/auth/register
2. Подтверждение     POST /api/auth/verify-email
3. Вход              POST /api/auth/login → JWT токен
4. Использование     Authorization: Bearer <токен>
```

## Регистрация

Регистрация разрешена **только** с корпоративной почтой `@utg.uz`.

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "ivanov@utg.uz",
  "password": "mypassword123",
  "full_name": "Иванов Иван"
}
```

**Ответ (201):**

```json
{
  "message": "Код подтверждения отправлен на вашу почту"
}
```

На указанный email будет отправлено письмо с 6-значным кодом подтверждения. Код действует 10 минут.

::: info Повторная регистрация
Если пользователь с таким email уже зарегистрирован, но ещё не подтвердил почту — его данные обновятся и код будет отправлен повторно.
:::

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| `409` | Email уже зарегистрирован (и подтверждён) |
| `422` | Невалидный email (не `@utg.uz`) |
| `500` | Ошибка отправки письма |

## Подтверждение email

```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "email": "ivanov@utg.uz",
  "code": "482901"
}
```

**Ответ (200):**

```json
{
  "message": "Email успешно подтверждён"
}
```

::: tip Суперадминистратор
Если email совпадает с `SUPERADMIN_EMAIL` из `.env`, пользователю автоматически назначается роль `superadmin` при подтверждении.
:::

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| `400` | Неверный/истёкший код, или email уже подтверждён |
| `404` | Пользователь не найден |

## Повторная отправка кода

Если код не пришёл или истёк:

```http
POST /api/auth/resend-code
Content-Type: application/json

{
  "email": "ivanov@utg.uz"
}
```

**Ответ (200):**

```json
{
  "message": "Код подтверждения отправлен повторно"
}
```

::: warning Ограничение
Между отправками должна пройти минимум 1 минута. При слишком частых запросах — ответ `429 Too Many Requests`.
:::

## Вход

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "ivanov@utg.uz",
  "password": "mypassword123"
}
```

**Ответ (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Токен действителен 24 часа (настраивается через `JWT_EXPIRATION_MINUTES`).

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| `401` | Неверный email или пароль |
| `403` | Email не подтверждён, или аккаунт заблокирован |

::: info Структурированная ошибка
При неподтверждённом email ответ содержит код для фронтенда:
```json
{
  "detail": {
    "message": "Email не подтверждён. Проверьте вашу почту.",
    "code": "email_not_verified"
  }
}
```
:::

## Использование токена

Передавайте токен в заголовке `Authorization` для всех защищённых эндпоинтов:

```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Ответ (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "ivanov@utg.uz",
  "full_name": "Иванов Иван",
  "phone": null,
  "auth_provider": "email",
  "is_active": true,
  "is_verified": true,
  "roles": ["admin"],
  "created_at": "2026-02-17T09:30:00Z"
}
```

## Сброс пароля

### Шаг 1: Запрос кода сброса

```http
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "ivanov@utg.uz"
}
```

**Ответ (200):**

```json
{
  "message": "Если аккаунт существует, код сброса отправлен на вашу почту"
}
```

::: info Безопасность
Ответ всегда одинаковый — независимо от того, существует ли аккаунт. Это предотвращает перечисление email.
:::

### Шаг 2: Установка нового пароля

```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "email": "ivanov@utg.uz",
  "code": "739201",
  "new_password": "mynewpassword456"
}
```

**Ответ (200):**

```json
{
  "message": "Пароль успешно изменён"
}
```

## Управление профилем

### Обновить ФИО

```http
PATCH /api/users/me
Authorization: Bearer <токен>
Content-Type: application/json

{
  "full_name": "Иванов Иван Петрович"
}
```

### Сменить пароль

```http
POST /api/users/me/change-password
Authorization: Bearer <токен>
Content-Type: application/json

{
  "current_password": "myoldpassword",
  "new_password": "mynewpassword456"
}
```

**Требования к паролю:** минимум 6 символов.

## Обработка 401 на фронтенде

Если токен истёк или стал невалидным, API вернёт `401 Unauthorized`. Фронтенд автоматически:
1. Очищает токен из `localStorage`
2. Сбрасывает состояние пользователя в Pinia-сторе
3. Перенаправляет на страницу входа (если текущая страница требует авторизации)
