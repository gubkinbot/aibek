# API — Администрирование

Все admin-эндпоинты находятся под префиксом `/api/admin` и требуют аутентификации + соответствующих permissions.

::: info Проверка доступа
Каждый эндпоинт проверяет наличие конкретного permission у пользователя. Суперадминистратор автоматически проходит все проверки. Permissions определяются уровнем доступа к модулю `admin`. Подробнее: [Система контроля доступа](../architecture/rbac).
:::

## Управление пользователями

### Список пользователей

```http
GET /api/admin/users?page=1&per_page=20&search=иванов&is_active=true
Authorization: Bearer <токен>
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `page` | int | Номер страницы (от 1) |
| `per_page` | int | Количество на странице (1–100, по умолчанию 20) |
| `search` | string | Поиск по ФИО, email, телефону |
| `is_active` | bool | Фильтр по статусу (активен/заблокирован) |

**Ответ (200):**

```json
{
  "items": [
    {
      "id": "550e8400-...",
      "email": "ivanov@utg.uz",
      "full_name": "Иванов Иван",
      "phone": null,
      "auth_provider": "email",
      "is_active": true,
      "is_verified": true,
      "is_superadmin": false,
      "created_at": "2026-02-17T09:30:00Z",
      "module_access": {
        "compressor": "operator",
        "admin": "viewer"
      }
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

**Permission:** `users.view`

### Детали пользователя

```http
GET /api/admin/users/{user_id}
```

Возвращает полную информацию, включая уровни доступа к модулям.

**Permission:** `users.view`

### Создать пользователя

```http
POST /api/admin/users
Content-Type: application/json

{
  "email": "petrov@utg.uz",
  "full_name": "Петров Пётр",
  "password": "optional-password",
  "module_access": {
    "compressor": "viewer",
    "admin": "viewer"
  }
}
```

Если `password` не указан, генерируется временный пароль и возвращается в ответе. Пользователь создаётся сразу верифицированным. Можно сразу назначить уровни доступа к модулям.

**Ответ (201):**

```json
{
  "message": "Пользователь petrov@utg.uz создан. Временный пароль: aB3dEf9x",
  "temp_password": "aB3dEf9x"
}
```

**Permission:** `users.create`

### Редактировать пользователя

```http
PATCH /api/admin/users/{user_id}
Content-Type: application/json

{
  "full_name": "Петров Пётр Сергеевич",
  "email": "p.petrov@utg.uz",
  "phone": "+998901234567"
}
```

Все поля опциональны — передавайте только то, что нужно изменить.

**Permission:** `users.edit`

### Заблокировать пользователя

```http
POST /api/admin/users/{user_id}/block
Content-Type: application/json

{
  "reason": "Нарушение правил использования"
}
```

Заблокированный пользователь не может войти в систему. Его `is_active` устанавливается в `false`, фиксируется дата и причина блокировки.

**Permission:** `users.block`

::: warning Защита
Суперадминистратора нельзя заблокировать. Попытка вернёт `403 Forbidden`.
:::

### Разблокировать пользователя

```http
POST /api/admin/users/{user_id}/unblock
```

**Permission:** `users.block`

### Сбросить пароль

```http
POST /api/admin/users/{user_id}/reset-password
```

Генерирует новый временный пароль. Если почта включена — отправляет его пользователю на email.

**Ответ (200):**

```json
{
  "message": "Пароль сброшен для petrov@utg.uz",
  "temp_password": "xK9mNp2v"
}
```

**Permission:** `users.reset_password`

### Удалить пользователя

```http
DELETE /api/admin/users/{user_id}
```

Полное удаление пользователя из базы данных.

**Ограничения:**
- Нельзя удалить суперадминистратора
- Нельзя удалить самого себя

**Permission:** `users.delete`

### Переключить суперадминистратора

```http
PUT /api/admin/users/{user_id}/superadmin
```

Переключает флаг `is_superadmin` (toggle): если был `true` — станет `false`, и наоборот.

**Ограничения:**
- Доступно **только суперадминистраторам**
- Нельзя изменить свой собственный статус

**Ответ (200):** Возвращает обновлённый объект пользователя.

---

## Управление уровнями доступа

### Список модулей и уровней

```http
GET /api/admin/module-access/levels
```

Возвращает все модули с доступными уровнями и permissions каждого уровня:

```json
{
  "admin": [
    {
      "level": "viewer",
      "display_name": "Наблюдатель",
      "description": "Просмотр пользователей и журнала",
      "permissions": ["users.view", "audit.view"]
    },
    {
      "level": "operator",
      "display_name": "Оператор",
      "description": "Управление пользователями",
      "permissions": ["users.view", "users.create", "users.edit", "users.delete", "users.block", "users.reset_password", "audit.view"]
    }
  ],
  "compressor": [
    {
      "level": "viewer",
      "display_name": "Наблюдатель",
      "permissions": ["compressor.access", "compressor.view"]
    },
    {
      "level": "operator",
      "display_name": "Оператор",
      "permissions": ["compressor.access", "compressor.view", "compressor.edit"]
    },
    {
      "level": "manager",
      "display_name": "Руководитель",
      "permissions": ["compressor.access", "compressor.view", "compressor.edit", "compressor.manage"]
    },
    {
      "level": "admin",
      "display_name": "Администратор",
      "permissions": ["compressor.access", "compressor.view", "compressor.edit", "compressor.manage", "compressor.admin"]
    }
  ]
}
```

**Permission:** `users.view`

### Получить уровни доступа пользователя

```http
GET /api/admin/module-access/users/{user_id}
```

Возвращает массив всех назначенных уровней доступа:

```json
[
  {
    "module": "compressor",
    "level": "operator",
    "permissions": ["compressor.access", "compressor.view", "compressor.edit"],
    "assigned_at": "2026-02-17T09:30:00Z",
    "assigned_by": "550e8400-..."
  },
  {
    "module": "admin",
    "level": "viewer",
    "permissions": ["users.view", "audit.view"],
    "assigned_at": "2026-02-18T10:00:00Z",
    "assigned_by": "550e8400-..."
  }
]
```

**Permission:** `users.view`

### Назначить уровень доступа

```http
PUT /api/admin/module-access/users/{user_id}
Content-Type: application/json

{
  "module": "compressor",
  "level": "manager"
}
```

Создаёт или обновляет (upsert) уровень доступа пользователя к модулю. У пользователя может быть **только один уровень на каждый модуль**.

**Ответ (200):**

```json
{
  "module": "compressor",
  "level": "manager",
  "permissions": ["compressor.access", "compressor.view", "compressor.edit", "compressor.manage"]
}
```

**Валидация:**
- Модуль должен быть из списка допустимых: `admin`, `compressor`, `balance`, `weather`, `digital`, `ai_chat`, `scada`
- Уровень должен быть допустим для модуля: `viewer`, `operator`, `manager`, `admin`

**Permission:** `users.edit`

### Удалить доступ к модулю

```http
DELETE /api/admin/module-access/users/{user_id}/{module}
```

Удаляет уровень доступа пользователя к указанному модулю.

**Permission:** `users.edit`

---

## Разрешения (Permissions)

### Список всех permissions

```http
GET /api/admin/permissions
```

Возвращает permissions, сгруппированные по категориям:

```json
[
  {
    "category": "users",
    "permissions": [
      {
        "id": "...",
        "codename": "users.view",
        "display_name": "Просмотр пользователей",
        "category": "users"
      },
      {
        "id": "...",
        "codename": "users.create",
        "display_name": "Создание пользователей",
        "category": "users"
      }
    ]
  },
  {
    "category": "compressor",
    "permissions": [
      {
        "id": "...",
        "codename": "compressor.access",
        "display_name": "Доступ к модулю компрессорных станций",
        "category": "compressor"
      }
    ]
  }
]
```

**Permission:** `users.view`

---

## Журнал действий (Audit Log)

### Получить журнал

```http
GET /api/admin/audit-logs?page=1&per_page=20&action=user.block&target_type=user
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `page` | int | Номер страницы |
| `per_page` | int | Количество на странице (1–100) |
| `actor_id` | UUID | Фильтр по автору действия |
| `action` | string | Фильтр по типу действия |
| `target_type` | string | Фильтр по типу объекта (`user`) |
| `target_id` | UUID | Фильтр по ID объекта |
| `date_from` | datetime | Начало периода |
| `date_to` | datetime | Конец периода |

**Ответ (200):**

```json
{
  "items": [
    {
      "id": "...",
      "actor_id": "uuid-admin",
      "actor_name": "Иванов Иван",
      "action": "user.module_access.set",
      "target_type": "user",
      "target_id": "uuid-пользователя",
      "details": {
        "module": "compressor",
        "old_level": "viewer",
        "new_level": "manager"
      },
      "ip_address": "10.1.30.50",
      "created_at": "2026-02-17T14:30:00Z"
    }
  ],
  "total": 120,
  "page": 1,
  "per_page": 20,
  "pages": 6
}
```

**Типы действий** (поле `action`):

| Действие | Описание |
|----------|----------|
| `user.create` | Создание пользователя |
| `user.edit` | Редактирование пользователя |
| `user.block` | Блокировка пользователя |
| `user.unblock` | Разблокировка пользователя |
| `user.delete` | Удаление пользователя |
| `user.reset_password` | Сброс пароля |
| `user.superadmin.toggle` | Переключение суперадмина |
| `user.module_access.set` | Назначение/изменение уровня доступа |
| `user.module_access.remove` | Удаление доступа к модулю |

**Permission:** `audit.view`

---

## Мониторинг системы

### Состояние сервисов

```http
GET /api/admin/system/status
```

Возвращает состояние трёх основных сервисов с подробными метриками:

**Backend (FastAPI):**
- Статус, аптайм, время сервера
- CPU загрузка, память (RAM), диск (used/total)
- Память процесса Python (`psutil`)

**База данных (PostgreSQL / TimescaleDB):**
- Версия PostgreSQL, аптайм
- Размер базы данных
- Активные соединения / максимум

**Redis:**
- Версия, аптайм
- Использование памяти
- Количество клиентов, ключей, обработанных команд

**Permission:** `system.view`

### История метрик сервера

```http
GET /api/admin/system/server-stats?count=120
```

Возвращает историю системных метрик хост-сервера (CPU, RAM, диск):

| Параметр | Тип | Описание |
|----------|-----|----------|
| `count` | int | Количество точек (по умолчанию 120) |

```json
{
  "points": [
    {
      "timestamp": "2026-02-17T14:30:00Z",
      "cpu_percent": 45.5,
      "memory_percent": 62.3,
      "disk_percent": 18.7
    }
  ]
}
```

**Permission:** `system.view`

### Docker-контейнеры — текущее состояние

```http
GET /api/admin/system/docker-stats
```

Возвращает последний снимок метрик всех Docker-контейнеров:

```json
{
  "latest": {
    "ts": 1771361390.97,
    "containers": {
      "aibek-backend-1": {
        "cpu_percent": 0.14,
        "memory_used": 109600768,
        "memory_limit": 16784982016,
        "memory_percent": 0.65,
        "status": "running"
      }
    }
  },
  "containers": ["aibek-backend-1", "aibek-db-1", "aibek-frontend-1", "..."]
}
```

**Permission:** `system.view`

### Docker-контейнеры — история

```http
GET /api/admin/system/docker-stats/{container_name}?count=120
```

Возвращает историю метрик контейнера из Redis Streams:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `container_name` | string | Имя контейнера (например, `aibek-backend-1`) |
| `count` | int | Количество точек (макс. 720, по умолчанию 120 = ~10 мин) |

```json
{
  "container": "aibek-backend-1",
  "points": [
    {
      "ts": 1771361278.341,
      "cpu": 0.13,
      "mem_used": 107483136,
      "mem_limit": 16784982016,
      "mem_pct": 0.64
    }
  ]
}
```

::: info Как это работает
Фоновая задача в backend каждые 5 секунд опрашивает Docker socket и записывает метрики в Redis Streams (`docker:stats:{container_name}`). Хранится до 720 точек на контейнер (~1 час истории). Данные не теряются при перезагрузке страницы.
:::

**Permission:** `system.view`
