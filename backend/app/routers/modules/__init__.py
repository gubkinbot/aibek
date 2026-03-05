"""Агрегация роутеров всех проектных модулей."""
from fastapi import APIRouter

from app.routers.modules import ai_chat, balance, compressor, digital, weather

router = APIRouter(prefix="/api/modules", tags=["modules"])

router.include_router(compressor.router)
router.include_router(balance.router)
router.include_router(weather.router)
router.include_router(digital.router)
router.include_router(ai_chat.router)
