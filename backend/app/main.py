from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, users
from app.services.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await redis_client.ping()
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
