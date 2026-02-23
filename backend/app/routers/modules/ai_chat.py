"""Роутер модуля «ИИ-чат»."""
from fastapi import APIRouter, Depends

from app.dependencies import require_permission

router = APIRouter(prefix="/ai-chat", tags=["module-ai-chat"])


@router.get("")
async def ai_chat_home(user=Depends(require_permission("ai_chat.access"))):
    """Главная страница модуля ИИ-чата."""
    return {"status": "ok", "module": "ai_chat"}
