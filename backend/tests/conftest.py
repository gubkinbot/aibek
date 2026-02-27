"""
Общие фикстуры для всех тестов.

Этот файл автоматически загружается pytest перед запуском тестов.
Здесь настраивается:
  - In-memory SQLite вместо PostgreSQL (тесты работают без Docker)
  - Фейковый Redis вместо реального (тесты работают без Redis-сервера)
  - HTTP-клиент для отправки запросов к FastAPI
  - Готовые пользователи и JWT-токены для тестов
"""

import os

# ──────────────────────────────────────────────────────────────
# Устанавливаем переменные окружения ДО импорта кода приложения.
# Это важно, потому что config.py читает их при первом импорте.
# ──────────────────────────────────────────────────────────────
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRATION_MINUTES"] = "60"
os.environ["REDIS_URL"] = "redis://fake"
os.environ["MAIL_ENABLED"] = "false"
os.environ["SUPERADMIN_EMAIL"] = ""

# ──────────────────────────────────────────────────────────────
# Подменяем PostgreSQL UUID на кроссплатформенный тип для SQLite.
# Модели используют sqlalchemy.dialects.postgresql.UUID, который
# не работает с SQLite. Наш тип принимает и строки, и uuid.UUID.
# Подмена делается ДО импорта моделей.
# ──────────────────────────────────────────────────────────────
import uuid as _uuid_mod
import sqlalchemy
import sqlalchemy.dialects.postgresql as pg_dialect
from sqlalchemy import String, TypeDecorator


class _UniversalUUID(TypeDecorator):
    """UUID-тип, работающий и с PostgreSQL, и с SQLite."""
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=True, **kw):
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return _uuid_mod.UUID(str(value))
        return value


pg_dialect.UUID = _UniversalUUID  # type: ignore[attr-defined]

import uuid
from unittest.mock import patch

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models.user import User
from app.services.auth import create_access_token, hash_password

# Импортируем приложение ПОСЛЕ установки переменных окружения
from app.main import app

# ──────────────────────────────────────────────────────────────
# Тестовая БД: SQLite в памяти (вместо PostgreSQL)
# ──────────────────────────────────────────────────────────────
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ──────────────────────────────────────────────────────────────
# Фейковый Redis (вместо реального Redis-сервера)
# ──────────────────────────────────────────────────────────────
fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)


# ──────────────────────────────────────────────────────────────
# Фикстура: сессия БД (создаёт таблицы, после теста — удаляет)
# ──────────────────────────────────────────────────────────────
@pytest.fixture
async def db_session():
    """Создаёт чистую БД для каждого теста."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ──────────────────────────────────────────────────────────────
# Фикстура: HTTP-клиент (подменяет БД и Redis)
# ──────────────────────────────────────────────────────────────
@pytest.fixture
async def client(db_session: AsyncSession):
    """
    HTTP-клиент для тестирования API.

    Подменяет get_db на тестовую сессию и redis_client на fakeredis
    во всех модулях, которые его используют.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Подменяем redis_client во всех модулях, которые его импортировали.
    # seed.py использует lazy import внутри функции, поэтому его не патчим здесь.
    patches = [
        patch("app.services.redis.redis_client", fake_redis),
        patch("app.services.verification.redis_client", fake_redis),
        patch("app.services.module_access.redis_client", fake_redis),
        patch("app.main.redis_client", fake_redis),
    ]

    for p in patches:
        p.start()

    # Очищаем fakeredis между тестами
    await fake_redis.flushall()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    for p in patches:
        p.stop()
    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────
# Фикстура: тестовый пользователь (верифицированный, активный)
# ──────────────────────────────────────────────────────────────
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Создаёт обычного пользователя в БД.
    Email: test@utg.uz, пароль: testpassword123
    """
    user = User(
        id=uuid.uuid4(),
        email="test@utg.uz",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ──────────────────────────────────────────────────────────────
# Фикстура: суперадмин
# ──────────────────────────────────────────────────────────────
@pytest.fixture
async def superadmin_user(db_session: AsyncSession) -> User:
    """
    Создаёт суперадмина в БД.
    Email: admin@utg.uz, пароль: adminpassword123
    """
    user = User(
        id=uuid.uuid4(),
        email="admin@utg.uz",
        hashed_password=hash_password("adminpassword123"),
        full_name="Super Admin",
        is_active=True,
        is_verified=True,
        is_superadmin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ──────────────────────────────────────────────────────────────
# Фикстура: заголовки с JWT-токеном обычного пользователя
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Возвращает HTTP-заголовки с JWT-токеном для test_user."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────
# Фикстура: заголовки с JWT-токеном суперадмина
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def superadmin_headers(superadmin_user: User) -> dict:
    """Возвращает HTTP-заголовки с JWT-токеном для superadmin_user."""
    token = create_access_token({"sub": str(superadmin_user.id)})
    return {"Authorization": f"Bearer {token}"}
