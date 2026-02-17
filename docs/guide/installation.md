# Установка и запуск

## Предварительные требования

| Компонент | Минимальная версия |
|-----------|-------------------|
| Docker | 24+ |
| Docker Compose | v2+ |
| Git | 2.40+ |

## Пошаговая установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/gubkinbot/aibek.git
cd aibek
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Откройте `.env` и настройте обязательные переменные:

```env
# Обязательно измените эти значения:
POSTGRES_PASSWORD=ваш_надёжный_пароль
JWT_SECRET=ваш_случайный_секретный_ключ

# Укажите email суперадминистратора:
SUPERADMIN_EMAIL=admin@utg.uz
```

::: warning Важно
`JWT_SECRET` и `POSTGRES_PASSWORD` **обязательно** нужно изменить перед развёртыванием. Используйте длинные случайные строки.
:::

::: tip Генерация секрета
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
:::

Полный список переменных — в разделе [Конфигурация](./configuration).

### 3. Запуск

```bash
docker compose up --build -d
```

Эта команда:
1. Собирает образы бэкенда и фронтенда
2. Поднимает TimescaleDB (PostgreSQL 16) с проверкой здоровья
3. Поднимает Redis с проверкой здоровья
4. Запускает бэкенд (FastAPI) — **после** готовности БД и Redis
5. Запускает фронтенд (Vite dev server)
6. Запускает VitePress (документация)
7. Запускает Nginx (reverse proxy)

### 4. Проверка

```bash
# Статус контейнеров (все должны быть healthy/running)
docker compose ps

# Проверка API
curl http://localhost/api/health
# Ответ: {"status": "ok"}

# Логи бэкенда (полезно при проблемах)
docker compose logs backend --tail 50
```

### 5. Инициализация данных

При первом запуске бэкенд автоматически:
- Создаёт все таблицы в базе данных
- Создаёт системные роли: `superadmin`, `admin`, `user`
- Создаёт 13 разрешений (permissions) по категориям
- Назначает роли `admin` все permissions кроме `roles.manage`
- Если `SUPERADMIN_EMAIL` задан и пользователь с таким email уже зарегистрирован и верифицирован — назначает ему роль `superadmin`

## Остановка

```bash
# Остановить все контейнеры (данные сохраняются)
docker compose down

# Остановить и удалить данные (volumes)
docker compose down -v
```

## Обновление

```bash
git pull
docker compose up --build -d
```

## Сервисы и порты

| Сервис | Контейнер | Внутренний порт | Внешний порт | Назначение |
|--------|-----------|----------------|-------------|-----------|
| Nginx | nginx | 80 | **80** | Reverse proxy (точка входа) |
| Backend | backend | 8000 | 8000 | FastAPI API |
| Frontend | frontend | 5173 | 5173 | Vue 3 (Vite dev server) |
| Docs | docs | 5174 | 5174 | VitePress документация |
| TimescaleDB | db | 5432 | 5432 | PostgreSQL база данных |
| Redis | redis | 6379 | 6379 | Кэш (коды верификации) |

::: info Маршрутизация Nginx
- `/` → Frontend (Vue 3)
- `/api/` → Backend (FastAPI)
- `/docs/` → Документация (VitePress)
:::

## Возможные проблемы

### Бэкенд не стартует

```bash
docker compose logs backend
```

Частые причины:
- БД ещё не готова — подождите 10–15 секунд, бэкенд перезапустится автоматически
- Неправильный `DATABASE_URL` — проверьте `.env`
- Порт 5432 занят локальным PostgreSQL

### Почта не отправляется

Проверьте настройки SMTP в `.env`:
```env
MAIL_SMTP_HOST=10.1.10.13
MAIL_SMTP_PORT=25
MAIL_FROM=ai@utg.uz
MAIL_ENABLED=true
```

Для локальной разработки без SMTP установите `MAIL_ENABLED=false` — коды будут выводиться в логи бэкенда.
