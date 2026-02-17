# Архитектура — Обзор

## Схема системы

```
┌─────────────────────────────────────────────────┐
│                  Nginx (:80)                     │
│        Reverse Proxy / Load Balancer             │
├──────────┬──────────────┬───────────────────────┤
│          │              │                        │
│  /       │  /api        │  /docs                 │
│  ↓       │  ↓           │  ↓                     │
│ Vue 3    │ FastAPI      │ VitePress              │
│ (:5173)  │ (:8000)      │ (:5174)                │
│          │              │                        │
│          ├──────┬───────┘                        │
│          │      │                                │
│          ↓      ↓                                │
│   TimescaleDB  Redis                             │
│    (:5432)    (:6379)                            │
└─────────────────────────────────────────────────┘
```

## Сервисы

| Сервис | Технология | Назначение |
|--------|-----------|------------|
| **Frontend** | Vue 3 + Vite + Tailwind | Веб-интерфейс платформы |
| **Backend** | FastAPI + SQLAlchemy | REST API, бизнес-логика |
| **Database** | TimescaleDB (PostgreSQL) | Хранение данных, временные ряды |
| **Cache** | Redis | Кэширование, сессии |
| **Docs** | VitePress | Документация проекта |
| **Proxy** | Nginx | Reverse proxy, маршрутизация |

## Структура проекта

```
aibek/
├── docker-compose.yml     # Оркестрация контейнеров
├── .env                   # Переменные окружения
├── nginx/                 # Конфигурация Nginx
├── backend/               # FastAPI приложение
│   └── app/
│       ├── main.py        # Точка входа
│       ├── models/        # SQLAlchemy модели
│       ├── schemas/       # Pydantic схемы
│       ├── routers/       # API эндпоинты
│       └── services/      # Бизнес-логика
├── frontend/              # Vue 3 приложение
│   └── src/
│       ├── views/         # Страницы
│       ├── components/    # Компоненты
│       ├── stores/        # Pinia (состояние)
│       └── api/           # HTTP клиент
└── docs/                  # VitePress документация
```

## Взаимодействие компонентов

1. **Пользователь** → Nginx (:80) → Frontend (Vue 3)
2. **Frontend** → Nginx → Backend (FastAPI) → TimescaleDB / Redis
3. **Документация** доступна через Nginx по `/docs/`
