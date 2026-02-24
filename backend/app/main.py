"""Точка входа FastAPI-приложения: инициализация, роутеры, фоновые задачи."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine, async_session
from app.routers import auth, users
from app.routers.admin import router as admin_router
from app.routers.modules import router as modules_router
from app.services.redis import redis_client
from app.services.seed import seed_permissions, ensure_superadmin, seed_default_access
from app.services.docker_monitor import collect_loop as docker_collect_loop
from app.services.server_monitor import collect_loop as server_collect_loop

# Ensure all models are imported so Base.metadata sees them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: создание таблиц, seed данных, запуск фоновых сборщиков метрик."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Конвертация time-series таблиц в TimescaleDB hypertables (идемпотентно)
        for table, interval in [
            ("compressor_tag_values", "1 day"),
            ("compressor_alarm_events", "7 days"),
            ("compressor_anomaly_events", "7 days"),
        ]:
            await conn.execute(text(
                f"SELECT create_hypertable('{table}', 'time', "
                f"chunk_time_interval => INTERVAL '{interval}', "
                f"if_not_exists => TRUE)"
            ))

    await redis_client.ping()

    # Seed system data
    async with async_session() as db:
        await seed_permissions(db)
        await ensure_superadmin(db)
    await seed_default_access()

    # Start background collectors
    docker_task = asyncio.create_task(docker_collect_loop())
    server_task = asyncio.create_task(server_collect_loop())

    yield

    docker_task.cancel()
    server_task.cancel()
    for task in (docker_task, server_task):
        try:
            await task
        except asyncio.CancelledError:
            pass
    await redis_client.aclose()


app = FastAPI(
    title="AI Platform - Узтрансгаз",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_router)
app.include_router(modules_router)


@app.get("/api/health")
async def health():
    """Проверка работоспособности API (health check)."""
    return {"status": "ok"}
