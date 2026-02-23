# Архитектура — Обзор

## Схема системы

```
┌──────────────────────────────────────────────────────────────┐
│                        Nginx (:80)                           │
│                    Reverse Proxy                             │
├──────────────────┬──────────────────┬────────────────────────┤
│                  │                  │                        │
│  /               │  /api            │  /docs                 │
│  ↓               │  ↓               │  ↓                     │
│  Vue 3           │  FastAPI         │  VitePress             │
│  (:5173)         │  (:8000)         │  (:5174)               │
│                  │                  │                        │
│  ┌────────────┐  │  ┌───────────┐   │                        │
│  │ Pinia      │  │  │ SQLAlchemy│   │                        │
│  │ Vue Router │  │  │ Pydantic  │   │                        │
│  │ Axios      │  │  │ JWT       │   │                        │
│  │ i18n       │  │  │ SMTP      │   │                        │
│  │ Chart.js   │  │  │ aiodocker │   │                        │
│  └────────────┘  │  └─────┬─────┘   │                        │
│                  │        │         │                        │
│                  │  ┌─────┴─────┐   │                        │
│                  │  │           │   │                        │
│                  │  ↓           ↓   │                        │
│              TimescaleDB     Redis  │                        │
│               (:5432)      (:6379)  │                        │
│                                     │                        │
│              Docker Socket (ro)     │                        │
│              /var/run/docker.sock   │                        │
└──────────────────────────────────────────────────────────────┘
```

## Сервисы

| Сервис | Технология | Назначение |
|--------|-----------|------------|
| **Frontend** | Vue 3 + Vite + Tailwind CSS | Веб-интерфейс: аутентификация, дашборд, модули, админ-панель |
| **Backend** | FastAPI + SQLAlchemy (async) | REST API, контроль доступа, аудит, бизнес-логика |
| **Database** | TimescaleDB (PostgreSQL 16) | Хранение данных: пользователи, уровни доступа, аудит |
| **Cache** | Redis 7 | Коды верификации, метрики Docker (Streams) |
| **Docs** | VitePress | Документация проекта |
| **Proxy** | Nginx | Reverse proxy, маршрутизация запросов |

## Структура проекта

```
aibek/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env / .env.example         # Переменные окружения
├── nginx/
│   └── nginx.conf              # Маршрутизация: /, /api, /docs
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
│       │   └── audit_log.py    # AuditLog (actor, action, target, details)
│       │
│       ├── schemas/            # Pydantic валидация запросов/ответов
│       │   ├── user.py         # UserCreate, UserLogin, UserResponse, Token
│       │   └── admin.py        # AdminUserResponse, SetModuleAccess, AuditLog
│       │
│       ├── routers/            # API эндпоинты
│       │   ├── auth.py         # /api/auth/* (регистрация, вход, верификация)
│       │   ├── users.py        # /api/users/* (профиль, смена пароля)
│       │   └── admin/          # /api/admin/*
│       │       ├── __init__.py     # Регистрация всех admin-роутеров
│       │       ├── users.py        # CRUD пользователей, toggle superadmin
│       │       ├── module_access.py # Управление уровнями доступа к модулям
│       │       ├── permissions.py  # Список permissions по категориям
│       │       ├── audit_logs.py   # Журнал действий с фильтрами
│       │       └── system.py       # Мониторинг системы и Docker
│       │
│       └── services/           # Бизнес-логика
│           ├── auth.py         # JWT: создание/декодирование токенов
│           ├── email.py        # Отправка писем (SMTP)
│           ├── verification.py # Коды верификации (Redis)
│           ├── redis.py        # Подключение к Redis
│           ├── seed.py         # Инициализация permissions и суперадмина
│           ├── module_access.py # Определение уровней доступа к модулям
│           ├── audit.py        # Запись действий в журнал аудита
│           ├── docker_monitor.py # Сбор метрик Docker → Redis Streams
│           └── server_monitor.py # Сбор метрик сервера (CPU, RAM, диск)
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
│       │   └── theme.js        # Тёмная/светлая тема
│       │
│       ├── router/
│       │   └── index.js        # Маршруты + guards (requiresAuth, guestOnly, requiresAdmin)
│       │
│       ├── components/
│       │   └── Navbar.vue      # Навигация: sidebar, admin-меню, тема, язык
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
│       │   │   └── AdminSystem.vue      # Мониторинг системы (Chart.js)
│       │   └── modules/        # Страницы модулей
│       │       ├── CompressorHome.vue   # Компрессорные станции
│       │       ├── BalanceHome.vue      # Балансировка ГТС
│       │       ├── WeatherHome.vue      # Погодные риски
│       │       ├── DigitalHome.vue      # Цифровой департамент
│       │       ├── AiChatHome.vue       # ИИ-чат
│       │       └── ScadaHome.vue        # SCADA
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
На странице: отображение уровня доступа и возможностей
```

## Инициализация при запуске

При старте бэкенда (в `lifespan`) последовательно выполняются:

1. **Создание таблиц** — `Base.metadata.create_all` создаёт все таблицы, если их нет
2. **Ping Redis** — проверка подключения к кэшу
3. **Seed permissions** — создание справочных permissions в БД (39 записей)
4. **Ensure superadmin** — если `SUPERADMIN_EMAIL` задан и пользователь верифицирован → `is_superadmin = true`
5. **Docker Monitor** — фоновая задача (`asyncio.create_task`), каждые 5 сек собирает CPU/RAM метрики контейнеров через Docker socket и записывает в Redis Streams
6. **Server Monitor** — фоновая задача, собирает метрики сервера (CPU, RAM, диск)

## Безопасность

- Все пароли хешируются через **bcrypt** (passlib)
- JWT подписывается секретным ключом (HS256)
- Корпоративная валидация email (`@utg.uz`)
- Обязательная верификация email перед входом
- Проверка permissions на каждом admin-эндпоинте через `require_permission()`
- Суперадмин определяется флагом `is_superadmin` — обходит все проверки доступа
- Защита суперадмина от блокировки/удаления
- IP-адреса записываются в аудит-лог
- Автоматический logout при 401 на фронтенде
- Docker socket монтируется **read-only** (`ro`) — только чтение метрик
