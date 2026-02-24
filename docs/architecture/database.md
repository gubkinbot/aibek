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

┌───────────────────────────┐     ┌───────────────────────────┐
│       permissions          │     │       audit_logs           │
│───────────────────────────│     │───────────────────────────│
│ id (UUID, PK)              │     │ id (UUID, PK)              │
│ codename (UNIQUE)          │     │ actor_id (FK → users)      │
│ display_name               │     │ action                     │
│ category                   │     │ target_type                │
└───────────────────────────┘     │ target_id                  │
                                   │ details (JSON)             │
                                   │ ip_address                 │
                                   │ created_at                 │
                                   └───────────────────────────┘

                    ┌─ Модуль «Компрессорные станции» (8 таблиц) ─┐
                    │ compressor_stations      → теги, computed    │
                    │ compressor_tags          → значения, аварии  │
                    │ compressor_computed_tags → вычисляемые       │
                    │ compressor_tag_values    → hypertable (1d)   │
                    │ compressor_alarm_rules   → правила аварий    │
                    │ compressor_alarm_events  → hypertable (7d)   │
                    │ compressor_anomaly_rules → детекторы          │
                    │ compressor_anomaly_events→ hypertable (7d)   │
                    └─────────────────────────────────────────────┘
```

Подробная схема компрессорных таблиц — в разделе [Модуль «Компрессорные станции»](#модуль-компрессорные-станции) ниже.

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

## Модуль «Компрессорные станции»

Таблицы модуля мониторинга компрессорных станций через OPC UA. Все модели определены в `backend/app/models/compressor.py`.

### ER-диаграмма компрессорного модуля

```
┌──────────────────────────────┐
│     compressor_stations       │
│──────────────────────────────│
│ id (UUID, PK)                 │
│ name, code (UNIQUE)           │
│ opc_url, opc_security_*       │
│ opc_cert_path, opc_key_path   │
│ polling_interval (300)        │
│ realtime_interval (1)         │
│ is_active, description        │
│ created_at, updated_at        │
└────────┬─────────┬───────────┘
         │         │
    1:N  │         │  1:N
         ▼         ▼
┌────────────────┐ ┌─────────────────────┐
│ compressor_tags │ │ compressor_computed_ │
│────────────────│ │ tags                 │
│ id, station_id  │ │─────────────────────│
│ opc_path, name  │ │ id, station_id       │
│ unit, data_type │ │ name, compute_type   │
│ category        │ │ config (JSON)        │
│ valid_min/max   │ │ category             │
│ stale_timeout   │ └─────────────────────┘
│ is_active       │
└───┬────┬────┬──┘
    │    │    │
    │    │    │  1:N
    │    │    ▼
    │    │ ┌──────────────────────┐
    │    │ │ compressor_alarm_rules│
    │    │ │──────────────────────│
    │    │ │ id, tag_id            │
    │    │ │ name, condition       │
    │    │ │ threshold, severity   │
    │    │ └──────┬───────────────┘
    │    │        │ 1:N
    │    │        ▼
    │    │ ┌──────────────────────┐
    │    │ │compressor_alarm_events│ ◄─ TimescaleDB hypertable
    │    │ │──────────────────────│
    │    │ │ time, rule_id, tag_id │
    │    │ │ station_id, value     │
    │    │ │ severity, message     │
    │    │ │ acknowledged          │
    │    │ └──────────────────────┘
    │    │
    │    │  1:N
    │    ▼
    │ ┌────────────────────────────┐
    │ │compressor_anomaly_rules     │
    │ │────────────────────────────│
    │ │ id, tag_id, detector_type   │
    │ │ config (JSON), severity     │
    │ └──────┬─────────────────────┘
    │        │ 1:N
    │        ▼
    │ ┌────────────────────────────┐
    │ │compressor_anomaly_events    │ ◄─ TimescaleDB hypertable
    │ │────────────────────────────│
    │ │ time, rule_id, tag_id       │
    │ │ station_id, detector_type   │
    │ │ details (JSON), severity    │
    │ │ acknowledged                │
    │ └────────────────────────────┘
    │
    │  1:N
    ▼
┌──────────────────────┐
│ compressor_tag_values  │ ◄─ TimescaleDB hypertable
│──────────────────────│
│ time, tag_id           │
│ value (Float)          │
│ quality (good/bad/     │
│  stale/outlier)        │
└──────────────────────┘
```

---

### Таблица `compressor_stations`

Конфигурация компрессорных станций с параметрами подключения к OPC UA серверам.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `name` | `String(100)` | NOT NULL | Название станции: «КС Ахангарон» |
| `code` | `String(50)` | UNIQUE, NOT NULL | Slug для URL и Redis ключей: `ahangaron` |
| `opc_url` | `String(255)` | NOT NULL | OPC UA URL: `opc.tcp://10.231.241.122:49320` |
| `opc_security_policy` | `String(100)` | default: `Basic128Rsa15` | Security Policy (Basic128Rsa15, Basic256, Basic256Sha256, None) |
| `opc_security_mode` | `String(50)` | default: `Sign` | Security Mode (Sign, SignAndEncrypt) |
| `opc_cert_path` | `String(255)` | nullable | Путь к сертификату клиента (DER) |
| `opc_key_path` | `String(255)` | nullable | Путь к приватному ключу (PEM) |
| `polling_interval` | `Integer` | default: `300` | Интервал записи истории (секунды) |
| `realtime_interval` | `Integer` | default: `1` | Интервал реалтайма (секунды) |
| `is_active` | `Boolean` | default: `true` | Коллектор опрашивает только активные станции |
| `description` | `Text` | nullable | Описание станции |
| `created_at` | `DateTime(tz)` | server_default: `now()` | Дата создания |
| `updated_at` | `DateTime(tz)` | onupdate: `now()` | Дата обновления |

**Связи:**

| Связь | Тип | Описание |
|-------|-----|----------|
| `tags` | One-to-Many → CompressorTag | Теги станции (CASCADE) |
| `computed_tags` | One-to-Many → CompressorComputedTag | Вычисляемые теги (CASCADE) |

---

### Таблица `compressor_tags`

Теги OPC UA — точки измерения на компрессорной станции.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `station_id` | `UUID` | FK → `compressor_stations.id`, CASCADE | Станция |
| `opc_path` | `String(255)` | NOT NULL | OPC-путь: `Channel1.Device1.Temperature` |
| `name` | `String(100)` | NOT NULL | Название: «Температура на входе» |
| `unit` | `String(50)` | nullable | Единица: `°C`, `bar`, `м³/ч` |
| `data_type` | `String(50)` | nullable | Тип данных: `Float`, `Int`, `Boolean` |
| `category` | `String(100)` | nullable | Группировка на UI: «Температура», «Давление» |
| `sort_order` | `Integer` | default: `0` | Порядок сортировки |
| `valid_min` | `Float` | nullable | Минимум диапазона — ниже → quality=`outlier` |
| `valid_max` | `Float` | nullable | Максимум диапазона — выше → quality=`outlier` |
| `stale_timeout` | `Integer` | nullable | Секунд без изменения → quality=`stale` |
| `is_active` | `Boolean` | default: `true` | Активен для опроса |
| `created_at` | `DateTime(tz)` | server_default: `now()` | Дата создания |

**Ограничения:** `UNIQUE(station_id, opc_path)` — один OPC-путь на станцию.

---

### Таблица `compressor_computed_tags`

Вычисляемые теги — агрегаты из нескольких OPC-тегов (статусы, формулы).

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `station_id` | `UUID` | FK → `compressor_stations.id`, CASCADE | Станция |
| `name` | `String(100)` | NOT NULL | Название: «Статус компрессора ГПА-1» |
| `unit` | `String(50)` | nullable | Единица (может быть NULL для статусов) |
| `category` | `String(100)` | nullable | Группировка: «Статус» |
| `sort_order` | `Integer` | default: `0` | Порядок |
| `compute_type` | `String(20)` | NOT NULL | Тип: `status_map` или `formula` |
| `config` | `JSON` | NOT NULL | Конфигурация (см. ниже) |
| `is_active` | `Boolean` | default: `true` | Активен |
| `created_at` | `DateTime(tz)` | server_default: `now()` | Дата создания |

**Форматы `config`:**

**`status_map`** — маппинг комбинации бинарных тегов в статус:
```json
{
  "source_tags": ["tag_uuid_1", "tag_uuid_2", "tag_uuid_3"],
  "rules": [
    {"when": {"tag_uuid_1": 0, "tag_uuid_2": 0, "tag_uuid_3": 1}, "status": "В работе", "value": 1},
    {"when": {"tag_uuid_1": 1, "tag_uuid_2": 0, "tag_uuid_3": 0}, "status": "На магистрали", "value": 2}
  ],
  "default": {"status": "Остановлен", "value": 0}
}
```

**`formula`** — арифметика из нескольких тегов:
```json
{
  "expression": "(a + b) / 2",
  "variables": {"a": "tag_uuid_temp1", "b": "tag_uuid_temp2"}
}
```

---

### Таблица `compressor_tag_values` (TimescaleDB hypertable)

Исторические значения тегов. Автоматически партиционируется по времени (chunk = 1 день).

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `time` | `DateTime(tz)` | PK, NOT NULL | Момент записи |
| `tag_id` | `UUID` | PK, FK → `compressor_tags.id` | Тег |
| `value` | `Float` | nullable | Значение (NULL при ошибке чтения) |
| `quality` | `String(20)` | default: `good` | Качество: `good`, `bad`, `stale`, `outlier` |

**Индексы:** `(tag_id, time DESC)` — для запросов `time_bucket()`.

---

### Таблица `compressor_alarm_rules`

Пороговые правила аварий для тегов.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `tag_id` | `UUID` | FK → `compressor_tags.id`, CASCADE | Тег |
| `name` | `String(200)` | NOT NULL | Название: «Высокая температура» |
| `condition` | `String(20)` | NOT NULL | Условие: `gt`, `lt`, `gte`, `lte` |
| `threshold` | `Float` | NOT NULL | Порог срабатывания |
| `severity` | `String(20)` | NOT NULL | Важность: `info`, `warning`, `critical` |
| `is_active` | `Boolean` | default: `true` | Активно |
| `created_at` | `DateTime(tz)` | server_default: `now()` | Дата создания |

---

### Таблица `compressor_alarm_events` (TimescaleDB hypertable)

Журнал аварийных событий. Chunk = 7 дней.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `time` | `DateTime(tz)` | PK, NOT NULL | Время события |
| `rule_id` | `UUID` | FK → `compressor_alarm_rules.id`, SET NULL | Правило |
| `tag_id` | `UUID` | FK → `compressor_tags.id` | Тег |
| `station_id` | `UUID` | PK, FK → `compressor_stations.id` | Станция |
| `value` | `Float` | | Значение в момент срабатывания |
| `threshold` | `Float` | | Порог |
| `severity` | `String(20)` | | Важность |
| `message` | `String(500)` | | Текст аварии |
| `acknowledged` | `Boolean` | default: `false` | Квитировано |
| `acknowledged_by` | `UUID` | FK → `users.id`, nullable | Кто квитировал |
| `acknowledged_at` | `DateTime(tz)` | nullable | Когда квитировано |

**Индексы:** `(station_id, time DESC)`.

---

### Таблица `compressor_anomaly_rules`

Правила детекции аномалий для тегов.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | `UUID` | PK, default: `uuid4` | Уникальный идентификатор |
| `tag_id` | `UUID` | FK → `compressor_tags.id`, CASCADE | Тег |
| `name` | `String(200)` | NOT NULL | Название: «Тренд роста температуры» |
| `detector_type` | `String(30)` | NOT NULL | Тип: `trend`, `volatility`, `stabilization`, `spike` |
| `config` | `JSON` | NOT NULL | Параметры детектора |
| `severity` | `String(20)` | NOT NULL | Важность |
| `is_active` | `Boolean` | default: `true` | Активно |
| `created_at` | `DateTime(tz)` | server_default: `now()` | Дата создания |

**Форматы `config` по типу детектора:**

| Тип | Параметры | Описание |
|-----|-----------|----------|
| `trend` | `window_minutes`, `slope_threshold`, `min_r_squared` | Линейная регрессия: аномалия если \|slope\| > threshold и R² > min |
| `volatility` | `window_minutes`, `baseline_minutes`, `std_multiplier` | Рост колебаний: std(current) > std(baseline) × multiplier |
| `stabilization` | `window_minutes`, `baseline_minutes`, `std_ratio_threshold` | Падение колебаний (залипание): std(current)/std(baseline) < threshold |
| `spike` | `window_minutes`, `sigma_threshold` | Z-score: \|value − mean\| > sigma × std |

---

### Таблица `compressor_anomaly_events` (TimescaleDB hypertable)

Журнал обнаруженных аномалий. Chunk = 7 дней.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `time` | `DateTime(tz)` | PK, NOT NULL | Время обнаружения |
| `rule_id` | `UUID` | FK → `compressor_anomaly_rules.id`, SET NULL | Правило |
| `tag_id` | `UUID` | FK → `compressor_tags.id` | Тег |
| `station_id` | `UUID` | PK, FK → `compressor_stations.id` | Станция |
| `detector_type` | `String(30)` | | Тип детектора |
| `value` | `Float` | | Текущее значение |
| `details` | `JSON` | | Подробности: slope, std, z_score и т.д. |
| `severity` | `String(20)` | | Важность |
| `message` | `String(500)` | | Описание аномалии |
| `acknowledged` | `Boolean` | default: `false` | Квитировано |
| `acknowledged_by` | `UUID` | FK → `users.id`, nullable | Кто квитировал |
| `acknowledged_at` | `DateTime(tz)` | nullable | Когда квитировано |

**Индексы:** `(station_id, time DESC)`.

---

## Каскадное удаление

**Платформенные таблицы:**
- При удалении **пользователя** — удаляются все его записи из `user_module_access`
- При удалении **пользователя** — в `audit_logs` поле `actor_id` устанавливается в `NULL`

**Компрессорный модуль:**
- При удалении **станции** — каскадно удаляются все теги, вычисляемые теги и связанные данные
- При удалении **тега** — каскадно удаляются правила аварий и аномалий
- При удалении **правила аварии/аномалии** — в журнале событий `rule_id` устанавливается в `NULL`

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
