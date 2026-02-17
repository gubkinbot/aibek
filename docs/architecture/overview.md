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
│  └────────────┘  │  └─────┬─────┘   │                        │
│                  │        │         │                        │
│                  │  ┌─────┴─────┐   │                        │
│                  │  │           │   │                        │
│                  │  ↓           ↓   │                        │
│              TimescaleDB     Redis  │                        │
│               (:5432)      (:6379)  │                        │
└──────────────────────────────────────────────────────────────┘
```

## Сервисы

| Сервис | Технология | Назначение |
|--------|-----------|------------|
| **Frontend** | Vue 3 + Vite + Tailwind CSS | Веб-интерфейс: аутентификация, дашборд, админ-панель |
| **Backend** | FastAPI + SQLAlchemy (async) | REST API, RBAC, аудит, бизнес-логика |
| **Database** | TimescaleDB (PostgreSQL 16) | Хранение всех данных: пользователи, роли, аудит |
| **Cache** | Redis 7 | Коды верификации, коды сброса пароля |
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
│       │   ├── user.py         # User (email, roles, groups, departments)
│       │   ├── role.py         # Role (name, display_name, is_system)
│       │   ├── permission.py   # Permission (codename, category)
│       │   ├── group.py        # Group (name, permissions, users)
│       │   ├── department.py   # Department (иерархия, users)
│       │   ├── associations.py # Связующие таблицы (M2M)
│       │   └── audit_log.py    # AuditLog (actor, action, target, details)
│       │
│       ├── schemas/            # Pydantic валидация запросов/ответов
│       │   ├── user.py         # UserCreate, UserLogin, UserResponse, Token
│       │   └── admin.py        # AdminUserResponse, RoleCreate, AuditLog и т.д.
│       │
│       ├── routers/            # API эндпоинты
│       │   ├── auth.py         # /api/auth/* (регистрация, вход, верификация)
│       │   ├── users.py        # /api/users/* (профиль, смена пароля)
│       │   └── admin/          # /api/admin/*
│       │       ├── __init__.py # Регистрация всех admin-роутеров
│       │       ├── users.py    # CRUD пользователей, назначение ролей/групп
│       │       ├── roles.py    # CRUD ролей, управление permissions
│       │       ├── groups.py   # CRUD групп, участники, permissions
│       │       ├── departments.py # CRUD подразделений (дерево)
│       │       ├── permissions.py # Список permissions по категориям
│       │       └── audit_logs.py  # Журнал действий с фильтрами
│       │
│       └── services/           # Бизнес-логика
│           ├── auth.py         # JWT: создание/декодирование токенов
│           ├── email.py        # Отправка писем (SMTP)
│           ├── verification.py # Коды верификации (Redis)
│           ├── redis.py        # Подключение к Redis
│           ├── seed.py         # Инициализация ролей и permissions
│           └── audit.py        # Запись действий в журнал аудита
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
│       │   ├── auth.js         # Аутентификация (user, token, login, logout)
│       │   ├── admin.js        # Админ-операции (CRUD пользователей/ролей/...)
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
│       │   └── admin/          # Админ-панель
│       │       ├── AdminUsers.vue       # Список пользователей
│       │       ├── AdminUserDetail.vue  # Карточка пользователя
│       │       ├── AdminRoles.vue       # Управление ролями
│       │       ├── AdminGroups.vue      # Управление группами
│       │       ├── AdminDepartments.vue # Управление подразделениями
│       │       └── AdminAuditLogs.vue   # Журнал действий
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

## Инициализация при запуске

При старте бэкенда (в `lifespan`) последовательно выполняются:

1. **Создание таблиц** — `Base.metadata.create_all` создаёт все таблицы, если их нет
2. **Ping Redis** — проверка подключения к кэшу
3. **Seed** — создание системных ролей и permissions, если их ещё нет
4. **Superadmin** — проверка и назначение роли суперадминистратора

## Безопасность

- Все пароли хешируются через **bcrypt** (passlib)
- JWT подписывается секретным ключом (HS256)
- Корпоративная валидация email (`@utg.uz`)
- Обязательная верификация email перед входом
- Проверка permissions на каждом admin-эндпоинте
- Защита суперадмина от блокировки/удаления
- IP-адреса записываются в аудит-лог
- Автоматический logout при 401 на фронтенде
