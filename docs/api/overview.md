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
| `GET` | `/api/auth/me` | Данные текущего пользователя (+ permissions, module_access) | JWT |

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
| `PUT` | `/api/admin/users/{id}/superadmin` | Переключить флаг суперадмина | Только суперадмин |

### Администрирование — Уровни доступа (`/api/admin/module-access`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/module-access/levels` | Все модули и уровни с permissions | `users.view` |
| `GET` | `/api/admin/module-access/users/{id}` | Уровни доступа пользователя | `users.view` |
| `PUT` | `/api/admin/module-access/users/{id}` | Назначить уровень доступа к модулю | `users.edit` |
| `DELETE` | `/api/admin/module-access/users/{id}/{module}` | Удалить доступ к модулю | `users.edit` |

### Администрирование — Разрешения (`/api/admin/permissions`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/permissions` | Список permissions по категориям | `users.view` |

### Администрирование — Журнал действий (`/api/admin/audit-logs`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/audit-logs` | Журнал действий (пагинация, фильтры) | `audit.view` |

### Администрирование — Система (`/api/admin/system`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `/api/admin/system/status` | Состояние сервисов (Backend, DB, Redis) | `system.view` |
| `GET` | `/api/admin/system/server-stats` | История метрик сервера (CPU, RAM, диск) | `system.view` |
| `GET` | `/api/admin/system/docker-stats` | Текущие метрики Docker-контейнеров | `system.view` |
| `GET` | `/api/admin/system/docker-stats/{name}` | История метрик контейнера (из Redis Streams) | `system.view` |

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
| `409` | Конфликт (дублирование email и т.д.) |
| `429` | Слишком много запросов (повторная отправка кода) |
| `500` | Внутренняя ошибка сервера |

## Подробнее

- [Аутентификация](./authentication) — полный цикл регистрации и входа
- [Администрирование](./admin) — детальное описание admin API
