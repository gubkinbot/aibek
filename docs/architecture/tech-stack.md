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
| asyncua | 1.1+ | OPC UA клиент для связи с Kepware и другими OPC-серверами |
| numpy | 1.26+ | Численные вычисления для детекторов аномалий |
| openpyxl | 3.1+ | Импорт/экспорт Excel файлов (теги, история) |
| cryptography | — | Генерация OPC UA сертификатов (RSA 2048, x509) |

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
| Chart.js | 4.5 | Графики: мониторинг Docker, исторические данные компрессоров |
| WebSocket (native) | — | Realtime обновления через браузерный WebSocket API |

## Инфраструктура

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Docker | 24+ | Контейнеризация |
| Docker Compose | v2 | Оркестрация 8 сервисов |
| Nginx | alpine | Reverse proxy, маршрутизация, WebSocket upgrade |
| TimescaleDB | PG 16 | PostgreSQL + hypertables для временных рядов |
| Redis | 7 | Кэш, pub/sub для realtime, хранилище метрик Docker (Streams) |
| VitePress | 1.5 | Документация проекта |

## Почему эти технологии?

### FastAPI
- Нативная поддержка `async/await` — эффективная обработка I/O
- Автоматическая документация (Swagger UI, ReDoc) из Pydantic-моделей
- Зависимости (Depends) — удобная система для авторизации и инъекции
- Встроенная поддержка WebSocket для realtime мониторинга

### Vue 3 + Composition API
- Реактивная система, удобная для сложных форм и таблиц
- Composition API позволяет переиспользовать логику через composables
- Отличная экосистема: Pinia, Vue Router, vue-i18n
- Composable `useCompressorWs` — реактивная обёртка над WebSocket

### SQLAlchemy 2.0 (async)
- Полноценный ORM с поддержкой сложных связей (many-to-many, self-referential)
- Async через asyncpg — без блокировки event loop
- `lazy="selectin"` — оптимизация загрузки связей
- Общие модели используются во всех 3 Python-контейнерах (backend, collector, analytics)

### TimescaleDB
- Полная совместимость с PostgreSQL (все расширения, SQL, инструменты)
- Hypertables для автоматического партиционирования time-series данных
- `time_bucket()` — агрегация исторических данных по произвольным интервалам
- Компрессия и партиционирование данных «из коробки»

### asyncua (OPC UA)
- Асинхронный клиент OPC UA — не блокирует event loop при работе с Kepware
- Поддержка Security Policy (Basic128Rsa15, Basic256, Basic256Sha256) и сертификатов
- Batch-чтение тегов через `asyncio.gather()` для высокой производительности
- Используется в отдельном контейнере `opc-collector`

### numpy
- Быстрые вычисления для детекторов аномалий (линейная регрессия, стандартное отклонение)
- Используется в отдельном контейнере `analytics`
- Минимальный overhead — только математические операции

### Tailwind CSS
- Утилитарный подход — стили прямо в шаблонах, не нужны отдельные CSS-файлы
- Встроенная поддержка `dark:` для тёмной темы
- Маленький размер финального CSS (tree-shaking)

### Redis
- Хранение кодов верификации и кодов сброса пароля с TTL
- Защита от повторной отправки (rate limiting)
- **Redis pub/sub** — realtime передача данных от opc-collector к backend WebSocket
- **Redis Streams** — time-series метрики Docker-контейнеров (CPU, память)
- **Redis SET с TTL** — snapshot состояния OPC и статусы подключений

### Chart.js
- Графики CPU и памяти Docker-контейнеров в реальном времени
- Исторические графики значений тегов компрессорных станций
- Лёгкий (tree-shakeable), без внешних зависимостей
- Хорошая интеграция с Vue 3 (через canvas ref)

### psutil + aiodocker
- `psutil` — метрики хоста (CPU, RAM, диск) изнутри backend-контейнера
- `aiodocker` — асинхронный доступ к Docker socket для сбора stats по всем контейнерам
- Docker socket монтируется read-only (`/var/run/docker.sock:ro`)

### openpyxl
- Импорт тегов и исторических данных из Excel (для массовой загрузки конфигурации)
- Генерация Excel-шаблонов со стилями и примерами данных
- Скачиваемые шаблоны для удобства пользователей
