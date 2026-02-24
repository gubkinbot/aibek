# AI-платформа АО «Узтрансгаз»

Корпоративная веб-платформа для работы с искусственным интеллектом, анализом данных и автоматизацией бизнес-процессов.

## Стек технологий

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic 2 |
| Frontend | Vue 3 (Composition API), Vite, Tailwind CSS, Pinia, Vue Router |
| OPC UA | asyncua — сбор данных с компрессорных станций (Kepware) |
| Аналитика | numpy — детекция аномалий (тренды, волатильность, выбросы) |
| БД | TimescaleDB (PostgreSQL 16) — hypertables для временных рядов |
| Кэш/Realtime | Redis 7 — pub/sub, snapshots, коды верификации |
| Инфраструктура | Docker Compose (8 контейнеров), Nginx |
| Документация | VitePress |

## Быстрый старт

```bash
git clone https://github.com/gubkinbot/aibek.git
cd aibek
cp .env.example .env   # отредактируйте переменные
docker compose up --build -d
```

Платформа будет доступна на `http://localhost` (или на IP сервера).

## Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Frontend   │◄-ws-│   Nginx:80  │     │  Kepware OPC UA  │
│  Vue 3      │     │             │     │  (10.231.x.x)    │
└─────────────┘     └──────┬──────┘     └────────┬─────────┘
                           │                      │ OPC UA (tcp)
                    ┌──────▼──────┐     ┌────────▼─────────┐
                    │   Backend   │     │  OPC Collector    │
                    │ FastAPI     │     │  per-station      │
                    │ REST + WS   │     │  workers          │
                    └──────┬──────┘     └────────┬─────────┘
                           │                      │
                    ┌──────▼──────────────────────▼──────┐
                    │    Redis (pub/sub + snapshots)      │
                    │    TimescaleDB (hypertables)        │
                    └──────────────┬─────────────────────┘
                                   │
                           ┌───────▼───────┐
                           │   Analytics   │
                           │  4 детектора  │
                           │  аномалий     │
                           └───────────────┘
```

**8 Docker-контейнеров:** db, redis, backend, opc-collector, analytics, frontend, docs, nginx.

## Основные возможности

- **Аутентификация** — регистрация с корпоративной почтой `@utg.uz`, подтверждение email, JWT-токены
- **RBAC** — модульная система контроля доступа: 7 модулей × 4 уровня = 39 permissions
- **Компрессорные станции** — мониторинг через OPC UA: realtime WebSocket, исторические графики, пороговые аварии, детекция аномалий (4 детектора)
- **Панель администрирования** — управление пользователями, доступами, настройками станций
- **Аудит** — журнал всех действий администраторов с IP-адресами
- **Мультиязычность** — русский и узбекский языки
- **Тёмная тема** — полная поддержка dark/light mode
- **Excel импорт/экспорт** — массовая загрузка тегов и исторических данных

## Структура проекта

```
aibek/
├── backend/           # FastAPI приложение
│   └── app/
│       ├── models/    # SQLAlchemy модели (User, Compressor*, AuditLog)
│       ├── schemas/   # Pydantic схемы валидации
│       ├── routers/   # API эндпоинты (/auth, /admin, /modules/compressor)
│       ├── services/  # Бизнес-логика (auth, email, audit, seed)
│       ├── collector/ # OPC-коллектор (main, worker, pipeline, certs)
│       ├── analytics/ # Детекция аномалий (main, detectors)
│       └── main.py    # Точка входа
├── frontend/          # Vue 3 приложение
│   └── src/
│       ├── views/     # Страницы (CompressorHome, Settings, admin/*)
│       ├── stores/    # Pinia (auth, admin, compressor)
│       ├── composables/ # useCompressorWs (WebSocket)
│       ├── components/# UI-компоненты (Navbar, PulseOrb)
│       ├── i18n/      # Переводы (ru, uz)
│       └── api/       # Axios HTTP-клиент
├── docs/              # VitePress документация
├── nginx/             # Nginx (reverse proxy + WebSocket)
├── opc-certs/         # OPC UA сертификаты (readonly)
├── docker-compose.yml # 8 контейнеров
└── .env.example
```

## Документация

Полная документация доступна по адресу `/docs/` после запуска проекта, или в папке `docs/`.

## Лицензия

Внутренний проект АО «Узтрансгаз». Все права защищены.
