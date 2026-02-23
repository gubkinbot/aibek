"""Роутер модуля «Балансировка ГТС»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/balance", tags=["module-balance"])


@router.get("")
async def balance_home(user=Depends(require_permission("balance.access"))):
    """Главная страница модуля балансировки ГТС."""
    return {"status": "ok", "module": "balance"}
