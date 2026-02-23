"""Роутер модуля «Погодные риски»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/weather", tags=["module-weather"])


@router.get("")
async def weather_home(user=Depends(require_permission("weather.access"))):
    """Главная страница модуля погодных рисков."""
    return {"status": "ok", "module": "weather"}
