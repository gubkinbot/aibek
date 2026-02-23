"""Подключение к базе данных: async SQLAlchemy engine, sessionmaker, базовый класс моделей."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


async def get_db():
    """Зависимость FastAPI: предоставляет асинхронную сессию БД."""
    async with async_session() as session:
        yield session
