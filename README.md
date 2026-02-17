# AI-платформа АО «Узтрансгаз»

Корпоративная веб-платформа для работы с искусственным интеллектом, анализом данных и автоматизацией бизнес-процессов.

## Стек технологий

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic 2 |
| Frontend | Vue 3 (Composition API), Vite, Tailwind CSS, Pinia, Vue Router |
| БД | TimescaleDB (PostgreSQL 16) |
| Кэш | Redis 7 |
| Инфраструктура | Docker Compose, Nginx |
| Документация | VitePress |

## Быстрый старт

```bash
git clone https://github.com/gubkinbot/aibek.git
cd aibek
cp .env.example .env   # отредактируйте переменные
docker compose up --build -d
```

Платформа будет доступна на `http://localhost` (или на IP сервера).

## Основные возможности

- **Аутентификация** — регистрация с корпоративной почтой `@utg.uz`, подтверждение email 6-значным кодом, JWT-токены
- **RBAC** — гибкие роли с динамическими permissions, группы доступа, организационная структура (подразделения)
- **Панель администрирования** — управление пользователями, ролями, группами, подразделениями
- **Аудит** — журнал всех действий администраторов с IP-адресами
- **Мультиязычность** — русский и узбекский языки
- **Тёмная тема** — полная поддержка dark/light mode

## Структура проекта

```
aibek/
├── backend/           # FastAPI приложение
│   └── app/
│       ├── models/    # SQLAlchemy модели (User, Role, Permission, Group, Department, AuditLog)
│       ├── schemas/   # Pydantic схемы валидации
│       ├── routers/   # API эндпоинты (/auth, /users, /admin/*)
│       ├── services/  # Бизнес-логика (auth, email, audit, seed)
│       └── main.py    # Точка входа
├── frontend/          # Vue 3 приложение
│   └── src/
│       ├── views/     # Страницы (Landing, Login, Register, Dashboard, Settings, admin/*)
│       ├── components/# UI-компоненты (Navbar)
│       ├── stores/    # Pinia-сторы (auth, admin)
│       ├── api/       # Axios HTTP-клиент
│       ├── i18n/      # Переводы (ru, uz)
│       └── utils/     # Утилиты (форматирование дат)
├── docs/              # VitePress документация
├── nginx/             # Конфигурация Nginx
├── docker-compose.yml
└── .env.example
```

## Документация

Полная документация доступна по адресу `/docs/` после запуска проекта, или в папке `docs/`.

## Лицензия

Внутренний проект АО «Узтрансгаз». Все права защищены.
