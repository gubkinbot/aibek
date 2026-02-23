# Стек технологий

## Backend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.12 | Язык программирования |
| FastAPI | 0.115 | Асинхронный веб-фреймворк с автодокументацией |
| SQLAlchemy | 2.0 | ORM (async через asyncpg) |
| Pydantic | 2.x | Валидация данных, настройки, схемы |
| python-jose | 3.3 | Создание и валидация JWT-токенов |
| passlib | 1.7 | Хеширование паролей (bcrypt) |
| uvicorn | 0.34 | ASGI-сервер |
| asyncpg | — | Асинхронный драйвер PostgreSQL |
| aiosmtplib | — | Асинхронная отправка email |
| redis (aioredis) | — | Асинхронный клиент Redis |
| psutil | 6.1 | Системные метрики (CPU, RAM, диск) |
| aiodocker | 0.23 | Асинхронный клиент Docker API |

## Frontend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Vue.js | 3.5 | UI-фреймворк (Composition API) |
| Vite | 6.0 | Сборка и dev-сервер |
| Tailwind CSS | 3.4 | CSS-утилиты + dark mode |
| Vue Router | 4.5 | Маршрутизация с navigation guards |
| Pinia | 2.3 | State management (реактивные сторы) |
| Axios | 1.7 | HTTP-клиент с interceptors |
| vue-i18n | 9.14 | Мультиязычность (ru/uz) |
| Chart.js | 4.5 | Графики мониторинга Docker-контейнеров и сервера |

## Инфраструктура

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Docker | 24+ | Контейнеризация |
| Docker Compose | v2 | Оркестрация сервисов |
| Nginx | alpine | Reverse proxy, маршрутизация |
| TimescaleDB | PG 16 | PostgreSQL + расширение для временных рядов |
| Redis | 7 | Кэш, хранилище метрик Docker (Streams) |
| VitePress | 1.5 | Документация проекта |

## Почему эти технологии?

### FastAPI
- Нативная поддержка `async/await` — эффективная обработка I/O
- Автоматическая документация (Swagger UI, ReDoc) из Pydantic-моделей
- Зависимости (Depends) — удобная система для авторизации и инъекции

### Vue 3 + Composition API
- Реактивная система, удобная для сложных форм и таблиц
- Composition API позволяет переиспользовать логику через composables
- Отличная экосистема: Pinia, Vue Router, vue-i18n

### SQLAlchemy 2.0 (async)
- Полноценный ORM с поддержкой сложных связей (many-to-many, self-referential)
- Async через asyncpg — без блокировки event loop
- `lazy="selectin"` — оптимизация загрузки связей

### TimescaleDB
- Полная совместимость с PostgreSQL (все расширения, SQL, инструменты)
- Расширение для временных рядов — пригодится для аналитики и мониторинга
- Компрессия и партиционирование данных «из коробки»

### Tailwind CSS
- Утилитарный подход — стили прямо в шаблонах, не нужны отдельные CSS-файлы
- Встроенная поддержка `dark:` для тёмной темы
- Маленький размер финального CSS (tree-shaking)

### Redis
- Хранение кодов верификации и кодов сброса пароля с TTL
- Защита от повторной отправки (rate limiting)
- **Redis Streams** для time-series метрик Docker-контейнеров (CPU, память)
- Снимки состояния контейнеров с автоочисткой (XTRIM maxlen)

### Chart.js
- Графики CPU и памяти Docker-контейнеров в реальном времени
- Лёгкий (tree-shakeable), без внешних зависимостей
- Хорошая интеграция с Vue 3 (через canvas ref)

### psutil + aiodocker
- `psutil` — метрики хоста (CPU, RAM, диск) изнутри backend-контейнера
- `aiodocker` — асинхронный доступ к Docker socket для сбора stats по всем контейнерам
- Docker socket монтируется read-only (`/var/run/docker.sock:ro`)
