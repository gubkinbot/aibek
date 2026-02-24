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

### Компрессорные станции (`/api/modules/compressor`)

| Метод | Путь | Описание | Permission |
|-------|------|----------|------------|
| `GET` | `.../stations` | Список станций | `compressor.view` |
| `GET` | `.../stations/{code}` | Детали станции | `compressor.view` |
| `GET` | `.../stations/{code}/status` | Статус OPC подключения | `compressor.view` |
| `POST` | `.../stations` | Создать станцию | `compressor.admin` |
| `PATCH` | `.../stations/{code}` | Обновить станцию | `compressor.admin` |
| `DELETE` | `.../stations/{code}` | Удалить станцию | `compressor.admin` |
| `POST` | `.../stations/{code}/generate-cert` | Генерация сертификата | `compressor.admin` |
| `GET` | `.../stations/{code}/download-cert` | Скачать сертификат (.der) | `compressor.admin` |
| `GET` | `.../stations/{code}/tags` | Теги станции | `compressor.view` |
| `POST` | `.../stations/{code}/tags` | Создать тег | `compressor.manage` |
| `POST` | `.../stations/{code}/tags/bulk` | Массовое создание | `compressor.manage` |
| `PATCH` | `.../tags/{tag_id}` | Обновить тег | `compressor.manage` |
| `DELETE` | `.../tags/{tag_id}` | Удалить тег | `compressor.manage` |
| `GET` | `.../tags/template-excel` | Шаблон Excel (теги) | `compressor.manage` |
| `GET` | `.../history/template-excel` | Шаблон Excel (история) | `compressor.manage` |
| `POST` | `.../stations/{code}/tags/import-excel` | Импорт тегов | `compressor.manage` |
| `POST` | `.../stations/{code}/history/import-excel` | Импорт истории | `compressor.manage` |
| `GET` | `.../stations/{code}/computed-tags` | Вычисляемые теги | `compressor.view` |
| `POST` | `.../stations/{code}/computed-tags` | Создать computed tag | `compressor.manage` |
| `PATCH` | `.../computed-tags/{ct_id}` | Обновить computed tag | `compressor.manage` |
| `DELETE` | `.../computed-tags/{ct_id}` | Удалить computed tag | `compressor.manage` |
| `GET` | `.../stations/{code}/realtime` | Snapshot значений | `compressor.view` |
| `GET` | `.../stations/{code}/history` | История (time_bucket) | `compressor.view` |
| `GET` | `.../stations/{code}/alarm-rules` | Правила аварий | `compressor.view` |
| `POST` | `.../stations/{code}/alarm-rules` | Создать правило | `compressor.manage` |
| `PATCH` | `.../alarm-rules/{rule_id}` | Обновить правило | `compressor.manage` |
| `DELETE` | `.../alarm-rules/{rule_id}` | Удалить правило | `compressor.manage` |
| `GET` | `.../stations/{code}/alarms` | Журнал аварий | `compressor.view` |
| `POST` | `.../alarms/acknowledge` | Квитировать аварию | `compressor.edit` |
| `GET` | `.../stations/{code}/anomaly-rules` | Правила аномалий | `compressor.view` |
| `POST` | `.../stations/{code}/anomaly-rules` | Создать правило | `compressor.manage` |
| `PATCH` | `.../anomaly-rules/{rule_id}` | Обновить правило | `compressor.manage` |
| `DELETE` | `.../anomaly-rules/{rule_id}` | Удалить правило | `compressor.manage` |
| `GET` | `.../stations/{code}/anomalies` | Журнал аномалий | `compressor.view` |
| `POST` | `.../anomalies/acknowledge` | Квитировать аномалию | `compressor.edit` |
| `WS` | `.../ws/{station_code}?token=JWT` | Realtime WebSocket | JWT |

Все пути начинаются с `/api/modules/compressor`.

## Подробнее

- [Аутентификация](./authentication) — полный цикл регистрации и входа
- [Администрирование](./admin) — детальное описание admin API
- [Компрессорные станции](./compressor) — полное описание API модуля мониторинга
