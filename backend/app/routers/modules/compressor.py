"""Роутер модуля «Компрессорные станции»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/compressor", tags=["module-compressor"])


@router.get("")
async def compressor_home(user=Depends(require_permission("compressor.access"))):
    """Главная страница модуля компрессорных станций."""
    return {"status": "ok", "module": "compressor"}
