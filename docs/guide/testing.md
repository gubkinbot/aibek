# Тестирование

Проект использует **pytest** с **pytest-asyncio** для автоматического тестирования бэкенда. Тесты работают без Docker — используется SQLite in-memory и fakeredis.

## Быстрый запуск

```bash
cd backend
pip install -r requirements.txt
python3 -m pytest -v
```

При каждом запуске автоматически генерируется JSON-отчёт (`test-report.json`), который отображается в админ-панели на странице мониторинга.

## Стек тестирования

| Технология | Назначение |
|-----------|------------|
| pytest | Фреймворк для запуска тестов |
| pytest-asyncio | Поддержка `async/await` в тестах |
| httpx + ASGITransport | HTTP-клиент для тестирования FastAPI без запуска сервера |
| aiosqlite | SQLite in-memory вместо PostgreSQL |
| fakeredis | In-memory Redis без настоящего Redis |
| pytest-json-report | Генерация JSON-отчёта для отображения в админке |

## Что тестируется

30 автотестов, разделённых по файлам:

| Файл | Тесты | Описание |
|------|-------|----------|
| `test_health.py` | 1 | Smoke-тест: `GET /api/health` |
| `test_auth_register.py` | 5 | Регистрация: успех, некорпоративная почта, дубликат, повторная отправка кода |
| `test_auth_login.py` | 5 | Логин: успех с JWT, неверный пароль, несуществующий email, неверифицированный, заблокированный |
| `test_auth_verify.py` | 6 | Верификация email: успех, неверный код, истёкший код, уже верифицирован |
| `test_auth_password.py` | 7 | Сброс пароля: запрос кода, rate limit, успешный сброс, неверный код |
| `test_users_profile.py` | 6 | Профиль: `/me`, обновление имени, смена пароля, невалидный токен |

## Архитектура тестов

### Fixtures (conftest.py)

```
conftest.py
├── db_session        # SQLite in-memory (создание/удаление таблиц per test)
├── client            # httpx.AsyncClient через ASGITransport
├── test_user         # Верифицированный пользователь (test@utg.uz)
├── superadmin_user   # Суперадминистратор (admin@utg.uz)
├── auth_headers      # JWT-заголовки для test_user
└── superadmin_headers # JWT-заголовки для superadmin_user
```

### Как это работает

1. **Замена БД**: SQLAlchemy подключается к `sqlite+aiosqlite:///:memory:` вместо PostgreSQL. Кастомный `_UniversalUUID` TypeDecorator обеспечивает совместимость UUID между PostgreSQL и SQLite.

2. **Замена Redis**: `fakeredis.aioredis.FakeRedis` заменяет настоящий Redis через `unittest.mock.patch`. Патчится во всех модулях, которые импортируют `redis_client`.

3. **HTTP без сервера**: `httpx.AsyncClient` + `ASGITransport` отправляют запросы напрямую в FastAPI-приложение, без запуска uvicorn.

4. **Изоляция тестов**: Каждый тест получает чистую базу данных (таблицы создаются и удаляются per test) и чистый Redis (flush per test).

## JSON-отчёт в админ-панели

При каждом запуске `pytest` генерируется `test-report.json`. Бэкенд предоставляет эндпоинт:

```
GET /api/admin/system/test-report
```

Результат отображается на странице мониторинга (`/admin/system`):
- Бейдж статуса: зелёный «Все пройдены» или красный «N не прошло»
- Дата последнего запуска и время выполнения
- Раскрывающийся список всех тестов с результатами

## Добавление новых тестов

1. Создайте файл `tests/test_<модуль>.py`
2. Используйте существующие fixtures из `conftest.py`:

```python
async def test_example(client, test_user, auth_headers):
    """Описание теста."""
    response = await client.get("/api/some-endpoint", headers=auth_headers)
    assert response.status_code == 200
```

3. Для работы с Redis напрямую импортируйте `fake_redis`:

```python
from tests.conftest import fake_redis

async def test_redis_example(client, test_user):
    await fake_redis.setex("some:key", 600, "value")
    # ... тест использующий Redis ...
```

4. Запустите тесты:

```bash
python3 -m pytest -v
```

::: tip Конфигурация
Настройки pytest находятся в `backend/pytest.ini`. JSON-отчёт генерируется автоматически через плагин `pytest-json-report`.
:::
