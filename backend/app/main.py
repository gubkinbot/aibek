from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine, async_session
from app.routers import auth, users
from app.routers.admin import router as admin_router
from app.services.redis import redis_client
from app.services.seed import seed_roles_and_permissions, ensure_superadmin

# Ensure all models are imported so Base.metadata sees them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await redis_client.ping()

    # Seed system data
    async with async_session() as db:
        await seed_roles_and_permissions(db)
        await ensure_superadmin(db)

    yield
    await redis_client.aclose()


app = FastAPI(
    title="AI Platform - Узтрансгаз",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
