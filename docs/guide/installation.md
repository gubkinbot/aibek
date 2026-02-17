# Установка и запуск

## Предварительные требования

| Компонент | Версия |
|-----------|--------|
| Docker | 24+ |
| Docker Compose | v2+ |
| Git | 2.40+ |

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/gubkinbot/aibek.git
cd aibek
```

### 2. Настройка переменных окружения

Скопируйте и отредактируйте файл `.env`:

```bash
cp .env.example .env
```

Основные переменные:

```env
POSTGRES_USER=aibek
POSTGRES_PASSWORD=<ваш_пароль>
POSTGRES_DB=aibek_db
JWT_SECRET=<ваш_секретный_ключ>
```

::: warning Важно
Обязательно измените `JWT_SECRET` и `POSTGRES_PASSWORD` перед развёртыванием в production.
:::

### 3. Запуск

```bash
docker compose up --build -d
```

### 4. Проверка

```bash
# Статус контейнеров
docker compose ps

# Проверка API
curl http://10.1.30.165/api/health
```

## Остановка

```bash
docker compose down
```

Для удаления данных (volumes):

```bash
docker compose down -v
```

## Обновление

```bash
git pull
docker compose up --build -d
```
