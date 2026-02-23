# Схема базы данных

Подробное описание всех таблиц, полей, связей и индексов базы данных платформы.

## Обзор

База данных работает на **TimescaleDB** (PostgreSQL 16) через асинхронный ORM **SQLAlchemy 2.0** с драйвером `asyncpg`. Все модели определены в `backend/app/models/`.

### ER-диаграмма

```
┌───────────────────────────┐
│          users             │
│───────────────────────────│
│ id (UUID, PK)              │
│ email (UNIQUE)             │
│ hashed_password            │
│ full_name                  │
│ phone (UNIQUE)             │
│ telegram_id (UNIQUE)       │
│ auth_provider              │
│ is_active                  │
│ is_verified                │
│ is_superadmin              │
│ blocked_at                 │
│ blocked_reason             │
│ created_at                 │
│ updated_at                 │
└────────┬──────────────────┘
         │
         │  1:N
         ▼
┌───────────────────────────┐
│    user_module_access      │
│───────────────────────────│
│ id (UUID, PK)              │
│ user_id (FK → users)       │
│ module (String)            │
│ level (String)             │
│ assigned_at                │
│ assigned_by (FK → users)   │
│                            │
│ UNIQUE(user_id, module)    │
└───────────────────────────┘

┌───────────────────────────┐
│       permissions          │
│───────────────────────────│
│ id (UUID, PK)              │
│ codename (UNIQUE)          │
│ display_name               │
│ category                   │
└───────────────────────────┘

┌───────────────────────────┐
│       audit_logs           │
│───────────────────────────│
│ id (UUID, PK)              │
│ actor_id (FK → users)      │
│ action                     │
│ target_type                │
│ target_id                  │
│ details (JSON)             │
│ ip_address                 │
│ created_at                 │
└───────────────────────────┘
```

---

## Таблица `users`

Основная таблица пользователей. Поддерживает несколько способов аутентификации (email, Telegram).

**Файл модели:** `backend/app/models/user.py`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `email` | `String(255)` | UNIQUE, INDEX, nullable | Корпоративная почта (`@utg.uz`) |
| `hashed_password` | `String(255)` | nullable | Хеш пароля (bcrypt) |
| `full_name` | `String(255)` | nullable | ФИО пользователя |
| `phone` | `String(20)` | UNIQUE, INDEX, nullable | Номер телефона |
| `telegram_id` | `BigInteger` | UNIQUE, INDEX, nullable | Telegram ID пользователя |
| `auth_provider` | `String(20)` | NOT NULL, default: `"email"` | Способ аутентификации: `email`, `telegram` |
| `is_active` | `Boolean` | NOT NULL, default: `true` | Активен ли аккаунт (false = заблокирован) |
| `is_verified` | `Boolean` | NOT NULL, default: `false` | Подтверждён ли email |
| `is_superadmin` | `Boolean` | NOT NULL, default: `false` | Флаг суперадминистратора (обходит все проверки permissions) |
| `blocked_at` | `DateTime(tz)` | nullable | Дата и время блокировки |
| `blocked_reason` | `String(500)` | nullable | Причина блокировки |
| `created_at` | `DateTime(tz)` | NOT NULL, server_default: `now()` | Дата создания аккаунта |
| `updated_at` | `DateTime(tz)` | nullable, onupdate: `now()` | Дата последнего обновления |

**Связи (relationships):**

| Связь | Тип | Описание | Lazy |
|-------|-----|----------|------|
| `module_access` | One-to-Many → UserModuleAccess | Уровни доступа к модулям | `selectin` |

**Индексы:** `email`, `phone`, `telegram_id` — для быстрого поиска при аутентификации.

---

## Таблица `user_module_access`

Уровни доступа пользователей к модулям. Каждая запись определяет уровень доступа конкретного пользователя к конкретному модулю.

**Файл модели:** `backend/app/models/module_access.py`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `user_id` | `UUID` | FK → `users.id`, INDEX, NOT NULL, ON DELETE CASCADE | Пользователь |
| `module` | `String(50)` | NOT NULL | Имя модуля: `admin`, `compressor`, `balance` и т.д. |
| `level` | `String(50)` | NOT NULL | Уровень доступа: `viewer`, `operator`, `manager`, `admin` |
| `assigned_at` | `DateTime(tz)` | NOT NULL, server_default: `now()` | Дата назначения |
| `assigned_by` | `UUID` | FK → `users.id`, nullable, ON DELETE SET NULL | Кто назначил доступ |

**Ограничения:**

| Тип | Поля | Описание |
|-----|------|----------|
| UNIQUE | `(user_id, module)` | У пользователя может быть только один уровень доступа на каждый модуль |

**Связи:**

| Связь | Тип | Описание | Lazy |
|-------|-----|----------|------|
| `user` | Many-to-One → User | Пользователь | `selectin` |

### Допустимые модули и уровни

Модули и уровни определены в `backend/app/services/module_access.py`:

**Модули:** `admin`, `compressor`, `balance`, `weather`, `digital`, `ai_chat`, `scada`

**Уровни:** `viewer`, `operator`, `manager`, `admin`

Каждая пара (module, level) автоматически транслируется в набор permissions. Подробнее — в разделе [Система контроля доступа](./rbac).

---

## Таблица `permissions`

Справочная таблица разрешений. Используется для отображения в UI и группировки по категориям. **Не используется для проверки доступа напрямую** — permissions вычисляются из `(module, level)` в runtime.

**Файл модели:** `backend/app/models/permission.py`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `codename` | `String(100)` | UNIQUE, INDEX, NOT NULL | Код разрешения: `users.view`, `compressor.edit` |
| `display_name` | `String(255)` | NOT NULL | Отображаемое имя: «Просмотр пользователей» |
| `category` | `String(50)` | INDEX, NOT NULL | Категория для группировки |

### Полный список permissions (seed)

**Административные:**

| Категория | codename | display_name |
|-----------|----------|-------------|
| **users** | `users.view` | Просмотр пользователей |
| **users** | `users.create` | Создание пользователей |
| **users** | `users.edit` | Редактирование пользователей |
| **users** | `users.delete` | Удаление пользователей |
| **users** | `users.block` | Блокировка пользователей |
| **users** | `users.reset_password` | Сброс пароля |
| **audit** | `audit.view` | Просмотр журнала действий |
| **system** | `system.view` | Просмотр мониторинга системы |
| **system** | `system.manage` | Управление системой |

**Модульные** (для каждого из 6 проектных модулей — compressor, balance, weather, digital, ai_chat, scada):

| Шаблон | Описание |
|--------|----------|
| `{module}.access` | Доступ к модулю (отображение в дашборде) |
| `{module}.view` | Просмотр данных модуля |
| `{module}.edit` | Работа с данными модуля |
| `{module}.manage` | Управление модулем |
| `{module}.admin` | Администрирование модуля |

Итого: 9 административных + 30 модульных = **39 permissions**.

---

## Таблица `audit_logs`

Журнал аудита всех административных действий. Записи создаются автоматически при выполнении admin-операций.

**Файл модели:** `backend/app/models/audit_log.py`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `actor_id` | `UUID` | FK → `users.id`, INDEX, nullable, ON DELETE SET NULL | Кто выполнил действие |
| `action` | `String(100)` | INDEX, NOT NULL | Тип действия |
| `target_type` | `String(50)` | INDEX, NOT NULL | Тип объекта: `user` |
| `target_id` | `UUID` | NOT NULL | ID объекта |
| `details` | `JSON` | nullable | Дополнительные данные (причина, старые/новые значения) |
| `ip_address` | `String(45)` | nullable | IP-адрес администратора |
| `created_at` | `DateTime(tz)` | NOT NULL, INDEX, server_default: `now()` | Время действия |

**Связи:**

| Связь | Тип | Описание | Lazy |
|-------|-----|----------|------|
| `actor` | Many-to-One → User | Пользователь, выполнивший действие | `selectin` |

### Типы действий (action)

| action | Описание |
|--------|----------|
| `user.create` | Создание пользователя через админ-панель |
| `user.edit` | Редактирование данных пользователя |
| `user.block` | Блокировка аккаунта |
| `user.unblock` | Разблокировка аккаунта |
| `user.delete` | Удаление пользователя |
| `user.reset_password` | Сброс пароля администратором |
| `user.superadmin.toggle` | Переключение флага суперадминистратора |
| `user.module_access.set` | Назначение/изменение уровня доступа к модулю |
| `user.module_access.remove` | Удаление доступа к модулю |

### Пример записи аудита

```json
{
  "id": "a1b2c3d4-...",
  "actor_id": "550e8400-...",
  "actor_name": "Иванов Иван",
  "action": "user.module_access.set",
  "target_type": "user",
  "target_id": "660f9500-...",
  "details": {
    "module": "compressor",
    "old_level": "viewer",
    "new_level": "manager"
  },
  "ip_address": "10.1.30.50",
  "created_at": "2026-02-17T14:30:00Z"
}
```

---

## Каскадное удаление

- При удалении **пользователя** — удаляются все его записи из `user_module_access`
- При удалении **пользователя** — в `audit_logs` поле `actor_id` устанавливается в `NULL`

::: warning Ограничения бизнес-логики
На уровне API есть дополнительные проверки (не на уровне БД):
- Нельзя удалить **суперадминистратора**
- Нельзя удалить **самого себя**
- Нельзя заблокировать **суперадминистратора**
:::

---

## Инициализация данных (Seed)

При первом запуске бэкенда (`lifespan`) выполняется:

1. **`seed_permissions()`** — создаются 39 permissions в справочной таблице (если не существуют)
2. **`ensure_superadmin()`** — если задан `SUPERADMIN_EMAIL` и пользователь уже верифицирован, ему ставится `is_superadmin = true`

```python
# Файл: backend/app/services/seed.py

async def seed_permissions(db):
    """Создание всех permissions (идемпотентно)."""
    for perm_data in PERMISSIONS:
        # CREATE IF NOT EXISTS
        ...

async def ensure_superadmin(db):
    """Установка флага is_superadmin для SUPERADMIN_EMAIL."""
    ...
```

---

## Миграции

Таблицы создаются автоматически при первом запуске через `Base.metadata.create_all()`. Для последующих изменений схемы используется Alembic:

```bash
# Создать миграцию
docker compose exec backend alembic revision --autogenerate -m "description"

# Применить миграции
docker compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker compose exec backend alembic downgrade -1
```
