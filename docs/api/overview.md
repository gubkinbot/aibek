# API — Обзор

Backend API построен на **FastAPI** и доступен по префиксу `/api`.

## Интерактивная документация

FastAPI автоматически генерирует интерактивную документацию:

- **Swagger UI**: `/api/docs` — можно тестировать запросы прямо в браузере
- **ReDoc**: `/api/redoc` — удобный справочник

## Аутентификация

API использует **JWT Bearer Token**. После логина передавайте токен в заголовке:

```
Authorization: Bearer <ваш_токен>
```

Подробнее: [Аутентификация](./authentication)

## Все эндпоинты

### Общие

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| `GET` | `/api/health` | Проверка состояния сервера | Нет |

### Аутентификация (`/api/auth`)

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| `POST` | `/api/auth/register` | Регистрация (только `@utg.uz`) | Нет |
| `POST` | `/api/auth/verify-email` | Подтверждение email по коду | Нет |
| `POST` | `/api/auth/resend-code` | Повторная отправка кода | Нет |
| `POST` | `/api/auth/login` | Вход, получение JWT | Нет |
| `POST` | `/api/auth/forgot-password` | Запрос сброса пароля | Нет |
| `POST` | `/api/auth/reset-password` | Сброс пароля по коду | Нет |
| `GET` | `/api/auth/me` | Данные текущего пользователя | JWT |

### Профиль пользователя (`/api/users`)

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| `PATCH` | `/api/users/me` | Обновить профиль (ФИО) | JWT |
| `POST` | `/api/users/me/change-password` | Сменить пароль | JWT |

### Администрирование — Пользователи (`/api/admin/users`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/users` | Список пользователей (пагинация, поиск, фильтры) | `users.view` |
| `GET` | `/api/admin/users/{id}` | Детали пользователя | `users.view` |
| `POST` | `/api/admin/users` | Создать пользователя | `users.create` |
| `PATCH` | `/api/admin/users/{id}` | Редактировать пользователя | `users.edit` |
| `POST` | `/api/admin/users/{id}/block` | Заблокировать | `users.block` |
| `POST` | `/api/admin/users/{id}/unblock` | Разблокировать | `users.block` |
| `POST` | `/api/admin/users/{id}/reset-password` | Сбросить пароль | `users.reset_password` |
| `DELETE` | `/api/admin/users/{id}` | Удалить пользователя | `users.delete` |
| `PUT` | `/api/admin/users/{id}/roles` | Назначить роли | `roles.manage` |
| `PUT` | `/api/admin/users/{id}/groups` | Назначить группы | `groups.manage` |
| `PUT` | `/api/admin/users/{id}/departments` | Назначить подразделения | `departments.manage` |

### Администрирование — Роли (`/api/admin/roles`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/roles` | Список ролей | `roles.view` |
| `POST` | `/api/admin/roles` | Создать роль | `roles.manage` |
| `GET` | `/api/admin/roles/{id}` | Детали роли с permissions | `roles.view` |
| `PATCH` | `/api/admin/roles/{id}` | Обновить роль | `roles.manage` |
| `DELETE` | `/api/admin/roles/{id}` | Удалить роль | `roles.manage` |
| `PUT` | `/api/admin/roles/{id}/permissions` | Установить permissions | `roles.manage` |

### Администрирование — Группы (`/api/admin/groups`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/groups` | Список групп | `groups.view` |
| `POST` | `/api/admin/groups` | Создать группу | `groups.manage` |
| `GET` | `/api/admin/groups/{id}` | Детали группы с permissions | `groups.view` |
| `PATCH` | `/api/admin/groups/{id}` | Обновить группу | `groups.manage` |
| `DELETE` | `/api/admin/groups/{id}` | Удалить группу | `groups.manage` |
| `PUT` | `/api/admin/groups/{id}/permissions` | Установить permissions | `groups.manage` |
| `PUT` | `/api/admin/groups/{id}/members` | Установить участников | `groups.manage` |

### Администрирование — Подразделения (`/api/admin/departments`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/departments` | Дерево подразделений | `departments.view` |
| `POST` | `/api/admin/departments` | Создать подразделение | `departments.manage` |
| `PATCH` | `/api/admin/departments/{id}` | Обновить подразделение | `departments.manage` |
| `DELETE` | `/api/admin/departments/{id}` | Удалить подразделение | `departments.manage` |
| `PUT` | `/api/admin/departments/{id}/members` | Установить участников | `departments.manage` |

### Администрирование — Разрешения (`/api/admin/permissions`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/permissions` | Список permissions по категориям | `roles.view` |

### Администрирование — Журнал действий (`/api/admin/audit-logs`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/audit-logs` | Журнал действий (пагинация, фильтры) | `audit.view` |

## Формат ответов

Все ответы возвращаются в формате JSON.

### Успешный ответ

```json
{
  "message": "Операция выполнена успешно"
}
```

### Пагинированный ответ

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Ошибка

```json
{
  "detail": "Описание ошибки"
}
```

### Коды ошибок

| Код | Значение |
|-----|----------|
| `400` | Некорректный запрос (валидация, бизнес-логика) |
| `401` | Не авторизован (токен отсутствует или невалиден) |
| `403` | Доступ запрещён (нет нужного permission) |
| `404` | Ресурс не найден |
| `409` | Конфликт (дублирование email, имени роли и т.д.) |
| `429` | Слишком много запросов (повторная отправка кода) |
| `500` | Внутренняя ошибка сервера |

## Подробнее

- [Аутентификация](./authentication) — полный цикл регистрации и входа
- [Администрирование](./admin) — детальное описание admin API
