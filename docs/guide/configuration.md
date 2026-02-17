# Конфигурация

Все параметры системы настраиваются через переменные окружения в файле `.env` в корне проекта.

## Переменные окружения

### База данных (TimescaleDB / PostgreSQL)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `POSTGRES_USER` | Имя пользователя БД | `aibek` |
| `POSTGRES_PASSWORD` | Пароль БД | `my_secure_password` |
| `POSTGRES_DB` | Имя базы данных | `aibek_db` |
| `DATABASE_URL` | Полный URL подключения | `postgresql+asyncpg://aibek:pass@db:5432/aibek_db` |

::: warning
`DATABASE_URL` должен использовать драйвер `postgresql+asyncpg` — бэкенд работает асинхронно.
:::

### Аутентификация (JWT)

| Переменная | Описание | По умолчанию |
|------------|----------|-------------|
| `JWT_SECRET` | Секретный ключ для подписи токенов | **обязательно задать** |
| `JWT_ALGORITHM` | Алгоритм подписи | `HS256` |
| `JWT_EXPIRATION_MINUTES` | Время жизни токена в минутах | `1440` (24 часа) |

### Redis

| Переменная | Описание | По умолчанию |
|------------|----------|-------------|
| `REDIS_URL` | URL подключения к Redis | `redis://redis:6379/0` |

Redis используется для хранения кодов верификации email и кодов сброса пароля. Коды живут 10 минут (600 секунд).

### Почта (SMTP)

| Переменная | Описание | По умолчанию |
|------------|----------|-------------|
| `MAIL_SMTP_HOST` | Адрес SMTP-сервера | `10.1.10.13` |
| `MAIL_SMTP_PORT` | Порт SMTP-сервера | `25` |
| `MAIL_FROM` | Email отправителя | `ai@utg.uz` |
| `MAIL_ENABLED` | Включить отправку писем | `true` |

::: tip Режим разработки
Установите `MAIL_ENABLED=false` для локальной разработки без SMTP. Коды подтверждения будут выводиться в логи бэкенда (`docker compose logs backend`).
:::

### Суперадминистратор

| Переменная | Описание | Пример |
|------------|----------|--------|
| `SUPERADMIN_EMAIL` | Email суперадминистратора | `admin@utg.uz` |

Когда пользователь с этим email подтверждает свою почту, ему автоматически назначается роль `superadmin`. Суперадминистратор обходит все проверки permissions и имеет полный доступ к системе.

### Верификация

| Переменная | Описание | По умолчанию |
|------------|----------|-------------|
| `VERIFICATION_CODE_TTL` | Время жизни кода верификации (секунды) | `600` (10 минут) |

## Пример полного .env

```env
# Database
POSTGRES_USER=aibek
POSTGRES_PASSWORD=my_secure_password_here
POSTGRES_DB=aibek_db
DATABASE_URL=postgresql+asyncpg://aibek:my_secure_password_here@db:5432/aibek_db

# JWT
JWT_SECRET=generate-a-random-secret-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Redis
REDIS_URL=redis://redis:6379/0

# Mail (SMTP relay)
MAIL_SMTP_HOST=10.1.10.13
MAIL_SMTP_PORT=25
MAIL_FROM=ai@utg.uz
MAIL_ENABLED=true

# Superadmin
SUPERADMIN_EMAIL=admin@utg.uz
```

## Порты

| Сервис | Внутренний | Внешний | Описание |
|--------|-----------|---------|----------|
| Nginx | 80 | **80** | Единая точка входа |
| Backend | 8000 | 8000 | API (через Nginx: `/api/`) |
| Frontend | 5173 | 5173 | Интерфейс (через Nginx: `/`) |
| Docs | 5174 | 5174 | Документация (через Nginx: `/docs/`) |
| TimescaleDB | 5432 | 5432 | База данных |
| Redis | 6379 | 6379 | Кэш |

::: info
В production рекомендуется закрыть все порты кроме 80 (Nginx) — все сервисы доступны через Nginx.
:::
