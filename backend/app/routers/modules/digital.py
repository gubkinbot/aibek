"""Роутер модуля «Цифровой департамент»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/digital", tags=["module-digital"])


@router.get("")
async def digital_home(user=Depends(require_permission("digital.access"))):
    """Главная страница модуля цифрового департамента."""
    return {"status": "ok", "module": "digital"}
