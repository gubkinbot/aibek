"""Роутер модуля «SCADA»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/scada", tags=["module-scada"])


@router.get("")
async def scada_home(user=Depends(require_permission("scada.access"))):
    """Главная страница модуля SCADA."""
    return {"status": "ok", "module": "scada"}
