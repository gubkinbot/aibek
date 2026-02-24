# Архитектура — Обзор

## Схема системы

```
┌──────────────────────────────────────────────────────────────────┐
│                          Nginx (:80)                              │
│                      Reverse Proxy + WebSocket                    │
├──────────────────┬──────────────────┬────────────────────────────┤
│                  │                  │                            │
│  /               │  /api            │  /docs                     │
│  ↓               │  ↓               │  ↓                         │
│  Vue 3           │  FastAPI         │  VitePress                 │
│  (:5173)         │  (:8000)         │  (:5174)                   │
│                  │  REST + WS       │                            │
│  ┌────────────┐  │  ┌───────────┐   │                            │
│  │ Pinia      │  │  │ SQLAlchemy│   │                            │
│  │ Vue Router │  │  │ Pydantic  │   │                            │
│  │ Axios      │  │  │ JWT       │   │                            │
│  │ WebSocket  │  │  │ SMTP      │   │                            │
│  │ Chart.js   │  │  │ aiodocker │   │                            │
│  └────────────┘  │  └─────┬─────┘   │                            │
│                  │        │         │                            │
│                  │  ┌─────┴─────┐   │                            │
│                  │  │           │   │                            │
│                  │  ↓           ↓   │                            │
│              TimescaleDB     Redis  │                            │
│               (:5432)      (:6379)  │                            │
│                                     │                            │
│              Docker Socket (ro)     │                            │
│              /var/run/docker.sock   │                            │
└──────────────────────────────────────────────────────────────────┘

               ┌────────────────────────┐     ┌────────────────┐
               │    opc-collector        │     │   analytics    │
               │  asyncio per-station    │────▶│  детекция      │
               │  OPC UA → Redis + DB    │     │  аномалий      │
               └───────────┬────────────┘     └───────┬────────┘
                           │                           │
                    ┌──────▼───────────────────────────▼──────┐
                    │         Redis (pub/sub + hash)           │
                    │         TimescaleDB (hypertables)        │
                    └─────────────────────────────────────────┘
```

## Сервисы

| Сервис | Технология | Назначение |
|--------|-----------|------------|
| **Frontend** | Vue 3 + Vite + Tailwind CSS | Веб-интерфейс: аутентификация, дашборд, модули, админ-панель |
| **Backend** | FastAPI + SQLAlchemy (async) | REST API + WebSocket, контроль доступа, аудит, бизнес-логика |
| **OPC Collector** | Python + asyncua | Сбор данных с OPC UA серверов компрессорных станций |
| **Analytics** | Python + numpy | Детекция аномалий (тренды, волатильность, выбросы, залипания) |
| **Database** | TimescaleDB (PostgreSQL 16) | Хранение данных: пользователи, теги, history (hypertables), аудит |
| **Cache** | Redis 7 | Коды верификации, realtime данные (pub/sub), статусы, метрики Docker |
| **Docs** | VitePress | Документация проекта |
| **Proxy** | Nginx | Reverse proxy, маршрутизация, WebSocket upgrade |

## Потоки данных

### OPC UA → Realtime мониторинг

```
Kepware OPC UA    →    opc-collector      →    Redis pub/sub    →    Backend WS    →    Vue 3
(10.231.x.x)          (per-station          (opc:realtime:{code})    (subscribe      (обновление
                        asyncio worker)      (opc:snapshot:{code})    + forward)       карточек)
                              │
                              ▼
                        TimescaleDB
                   (compressor_tag_values)
```

### Пороговые аварии

```
opc-collector    →    check_alarms()    →    Redis pub/sub         →    Backend WS    →    Vue 3
(чтение тегов)       (condition > threshold)  (opc:alarms:{code})       (forward)       (уведомление)
                              │
                              ▼
                        TimescaleDB
                   (compressor_alarm_events)
```

### Детекция аномалий

```
analytics        →    TimescaleDB        →    detectors            →    Redis pub/sub      →    Vue 3
(каждые 60с)         (запрос окна данных)     (trend, volatility,       (opc:anomalies:{code})  (уведомление)
                                               spike, stabilization)
                                                      │
                                                      ▼
                                                TimescaleDB
                                           (compressor_anomaly_events)
```

## Структура проекта

```
aibek/
├── docker-compose.yml          # Оркестрация всех сервисов (8 контейнеров)
├── .env / .env.example         # Переменные окружения
├── nginx/
│   └── nginx.conf              # Маршрутизация: /, /api, /docs + WebSocket
├── opc-certs/                  # OPC UA сертификаты (readonly mount)
│
├── backend/                    # FastAPI приложение
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # Точка входа, lifespan (создание таблиц, seed)
│       ├── config.py           # Настройки из .env (Pydantic Settings)
│       ├── database.py         # Подключение к БД (async SQLAlchemy)
│       ├── dependencies.py     # FastAPI зависимости (auth, permissions)
│       │
│       ├── models/             # SQLAlchemy ORM модели
│       │   ├── user.py         # User (email, is_superadmin, module_access)
│       │   ├── module_access.py # UserModuleAccess (module, level)
│       │   ├── permission.py   # Permission (codename, category) — справочник
│       │   ├── audit_log.py    # AuditLog (actor, action, target, details)
│       │   └── compressor.py   # 8 таблиц компрессорного модуля
│       │
│       ├── schemas/            # Pydantic валидация запросов/ответов
│       │   ├── user.py         # UserCreate, UserLogin, UserResponse, Token
│       │   ├── admin.py        # AdminUserResponse, SetModuleAccess, AuditLog
│       │   └── compressor.py   # Station, Tag, Alarm, Anomaly, History, Realtime
│       │
│       ├── routers/            # API эндпоинты
│       │   ├── auth.py         # /api/auth/* (регистрация, вход, верификация)
│       │   ├── users.py        # /api/users/* (профиль, смена пароля)
│       │   ├── admin/          # /api/admin/*
│       │   │   ├── __init__.py     # Регистрация admin-роутеров
│       │   │   ├── users.py        # CRUD пользователей, toggle superadmin
│       │   │   ├── module_access.py # Управление уровнями доступа
│       │   │   ├── permissions.py  # Список permissions по категориям
│       │   │   ├── audit_logs.py   # Журнал действий с фильтрами
│       │   │   └── system.py       # Мониторинг системы и Docker
│       │   └── modules/        # /api/modules/*
│       │       ├── __init__.py     # Агрегация модульных роутеров
│       │       ├── compressor.py   # 35 REST + 1 WebSocket эндпоинт
│       │       ├── balance.py
│       │       ├── weather.py
│       │       ├── digital.py
│       │       ├── ai_chat.py
│       │       └── scada.py
│       │
│       ├── services/           # Бизнес-логика
│       │   ├── auth.py         # JWT: создание/декодирование токенов
│       │   ├── email.py        # Отправка писем (SMTP)
│       │   ├── verification.py # Коды верификации (Redis)
│       │   ├── redis.py        # Подключение к Redis
│       │   ├── seed.py         # Инициализация permissions и суперадмина
│       │   ├── module_access.py # Определение уровней доступа к модулям
│       │   ├── audit.py        # Запись действий в журнал аудита
│       │   ├── docker_monitor.py # Сбор метрик Docker → Redis Streams
│       │   └── server_monitor.py # Сбор метрик сервера (CPU, RAM, диск)
│       │
│       ├── collector/          # OPC-коллектор (отдельный процесс)
│       │   ├── __init__.py
│       │   ├── main.py         # Entrypoint: python -m app.collector.main
│       │   ├── worker.py       # Per-station OPC UA worker
│       │   ├── pipeline.py     # Валидация + вычисляемые теги
│       │   └── certs.py        # Генерация OPC UA сертификатов
│       │
│       └── analytics/          # Сервис аналитики (отдельный процесс)
│           ├── __init__.py
│           ├── main.py         # Entrypoint: python -m app.analytics.main
│           └── detectors.py    # 4 детектора аномалий
│
├── frontend/                   # Vue 3 приложение
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── main.js             # Точка входа (Pinia, Router, i18n)
│       ├── App.vue             # Корневой компонент
│       ├── style.css           # Tailwind CSS
│       │
│       ├── api/
│       │   └── index.js        # Axios: baseURL, JWT interceptor, 401 обработка
│       │
│       ├── stores/             # Pinia сторы (состояние)
│       │   ├── auth.js         # Аутентификация (user, token, permissions)
│       │   ├── admin.js        # Админ-операции (CRUD пользователей, доступ)
│       │   ├── theme.js        # Тёмная/светлая тема
│       │   └── compressor.js   # Компрессорный модуль (26 actions, WS handling)
│       │
│       ├── composables/
│       │   └── useCompressorWs.js  # WebSocket с auto-reconnect
│       │
│       ├── router/
│       │   └── index.js        # Маршруты + guards
│       │
│       ├── components/
│       │   ├── Navbar.vue      # Навигация: sidebar, admin-меню, тема, язык
│       │   ├── PulseOrb.vue    # Анимированный фон для дашборда
│       │   └── AuthLayout.vue  # Layout для auth-страниц
│       │
│       ├── views/              # Страницы
│       │   ├── Landing.vue     # Главная (для неавторизованных)
│       │   ├── Login.vue       # Вход
│       │   ├── Register.vue    # Регистрация
│       │   ├── VerifyEmail.vue # Подтверждение email
│       │   ├── ForgotPassword.vue # Сброс пароля
│       │   ├── Dashboard.vue   # Дашборд (для авторизованных)
│       │   ├── Settings.vue    # Настройки профиля
│       │   ├── admin/          # Админ-панель
│       │   │   ├── AdminUsers.vue       # Список пользователей
│       │   │   ├── AdminUserDetail.vue  # Карточка пользователя
│       │   │   ├── AdminAuditLogs.vue   # Журнал действий
│       │   │   ├── AdminSystem.vue      # Мониторинг системы
│       │   │   └── AdminCompressor.vue  # Настройки компрессорных станций
│       │   └── modules/        # Страницы модулей
│       │       ├── CompressorHome.vue      # Мониторинг (realtime, аварии, графики)
│       │       ├── CompressorSettings.vue  # Настройки (теги, правила, импорт)
│       │       ├── BalanceHome.vue
│       │       ├── WeatherHome.vue
│       │       ├── DigitalHome.vue
│       │       ├── AiChatHome.vue
│       │       └── ScadaHome.vue
│       │
│       ├── i18n/               # Мультиязычность
│       │   ├── index.js        # Настройка vue-i18n
│       │   ├── ru.js           # Русский язык
│       │   └── uz.js           # Узбекский язык
│       │
│       └── utils/
│           └── date.js         # Форматирование дат через i18n
│
└── docs/                       # VitePress документация
    ├── Dockerfile
    ├── package.json
    └── *.md                    # Страницы документации
```

## Как работает запрос

### Обычный пользователь

```
Браузер → Nginx (:80) → Vue 3 (:5173) → отрисовка страницы
    ↓
Vue (Axios) → Nginx (/api/*) → FastAPI (:8000)
    ↓
FastAPI → JWT проверка → SQLAlchemy → PostgreSQL
    ↓
Ответ JSON → Vue → отображение данных
```

### Администратор

```
Администратор → /admin/users → Vue компонент AdminUsers.vue
    ↓
Pinia admin store → Axios GET /api/admin/users
    ↓
FastAPI → JWT → require_permission("users.view") → SQL запрос
    ↓
Ответ с пагинацией → Pinia → таблица пользователей в UI
```

### Проверка доступа к модулю

```
Пользователь → /compressor → Vue CompressorHome.vue
    ↓
Router guard → auth.hasPermission("compressor.access")
    ↓
Проверка: user.module_access содержит "compressor" → разрешить
    ↓
На странице: realtime данные через WebSocket, история через REST
```

### Realtime мониторинг (OPC UA → WebSocket)

```
opc-collector → читает OPC теги каждые 1 сек
    ↓
DataPipeline → validate, stale detect, compute → Redis PUBLISH
    ↓
Backend WebSocket → подписан на Redis → forward клиенту
    ↓
Vue (useCompressorWs) → store.handleWsMessage → реактивное обновление UI
```

## Инициализация при запуске

При старте бэкенда (в `lifespan`) последовательно выполняются:

1. **Создание таблиц** — `Base.metadata.create_all` создаёт все таблицы, включая компрессорные (+ TimescaleDB hypertables)
2. **Ping Redis** — проверка подключения к кэшу
3. **Seed permissions** — создание справочных permissions в БД (39 записей)
4. **Ensure superadmin** — если `SUPERADMIN_EMAIL` задан и пользователь верифицирован → `is_superadmin = true`
5. **Docker Monitor** — фоновая задача, каждые 5 сек собирает метрики контейнеров → Redis Streams
6. **Server Monitor** — фоновая задача, собирает метрики сервера (CPU, RAM, диск)

::: info OPC-коллектор и Analytics
Коллектор и аналитика работают в **отдельных контейнерах** (`opc-collector`, `analytics`), не внутри backend. Они используют ту же кодовую базу (`build: ./backend`) с разными `command`.
:::

## Redis ключи (компрессорный модуль)

| Ключ | Тип | TTL | Описание |
|------|-----|-----|----------|
| `opc:realtime:{code}` | pub/sub канал | — | JSON snapshot всех тегов станции |
| `opc:alarms:{code}` | pub/sub канал | — | JSON аварийного события |
| `opc:anomalies:{code}` | pub/sub канал | — | JSON аномалии |
| `opc:snapshot:{code}` | STRING | 10s | Последний snapshot (для REST) |
| `opc:status:{code}` | STRING | 30s | Статус подключения: connected, error, tags_count |

## Безопасность

- Все пароли хешируются через **bcrypt** (passlib)
- JWT подписывается секретным ключом (HS256)
- Корпоративная валидация email (`@utg.uz`)
- Обязательная верификация email перед входом
- Проверка permissions на каждом эндпоинте через `require_permission()`
- Суперадмин определяется флагом `is_superadmin` — обходит все проверки доступа
- Защита суперадмина от блокировки/удаления
- IP-адреса записываются в аудит-лог
- Автоматический logout при 401 на фронтенде
- Docker socket монтируется **read-only** (`ro`) — только чтение метрик
- OPC UA сертификаты генерируются per-station (RSA 2048, DER/PEM)
- Директория `opc-certs/` монтируется **read-only** в контейнер коллектора
- WebSocket аутентификация через JWT в query parameter
