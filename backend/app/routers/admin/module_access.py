"""Admin-роутер управления уровнями доступа к модулям."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_client_ip, require_permission
from app.models.module_access import UserModuleAccess
from app.models.user import User
from app.schemas.admin import AdminMessageResponse, SetModuleAccessRequest
from app.services.audit import log_action
from app.services.module_access import (
    MODULE_ACCESS_LEVELS,
    get_permissions_for_module_level,
    get_valid_levels,
    get_valid_modules,
)

router = APIRouter(prefix="/module-access", tags=["admin-module-access"])


@router.get("/levels")
async def list_module_levels(
    current_user: User = Depends(require_permission("users.view")),
):
    """Возвращает все модули и определения их уровней доступа."""
    return MODULE_ACCESS_LEVELS


@router.get("/users/{user_id}")
async def get_user_module_access(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    """Получает все назначенные уровни доступа пользователя к модулям."""
    result = await db.execute(
        select(UserModuleAccess).where(UserModuleAccess.user_id == user_id)
    )
    assignments = result.scalars().all()
    return [
        {
            "module": a.module,
            "level": a.level,
            "assigned_at": a.assigned_at,
            "permissions": sorted(get_permissions_for_module_level(a.module, a.level)),
        }
        for a in assignments
    ]


@router.put("/users/{user_id}")
async def set_user_module_access(
    user_id: uuid.UUID,
    data: SetModuleAccessRequest,
    request: Request,
    current_user: User = Depends(require_permission("users.roles.assign")),
    db: AsyncSession = Depends(get_db),
):
    """Назначает (создаёт или обновляет) уровень доступа пользователя к модулю."""
    if data.module not in get_valid_modules():
        raise HTTPException(status_code=400, detail=f"Неизвестный модуль: {data.module}")
    if data.level not in get_valid_levels(data.module):
        raise HTTPException(status_code=400, detail=f"Неизвестный уровень: {data.level}")

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Upsert
    result = await db.execute(
        select(UserModuleAccess).where(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.module == data.module,
        )
    )
    existing = result.scalar_one_or_none()

    old_level = None
    if existing:
        old_level = existing.level
        existing.level = data.level
        existing.assigned_by = current_user.id
    else:
        ma = UserModuleAccess(
            user_id=user_id,
            module=data.module,
            level=data.level,
            assigned_by=current_user.id,
        )
        db.add(ma)

    await log_action(
        db, current_user.id, "user.module_access.set", "user", user_id,
        details={"module": data.module, "old_level": old_level, "new_level": data.level},
        ip_address=get_client_ip(request),
    )
    await db.commit()

    return {
        "module": data.module,
        "level": data.level,
        "permissions": sorted(get_permissions_for_module_level(data.module, data.level)),
    }


@router.delete("/users/{user_id}/{module}")
async def remove_user_module_access(
    user_id: uuid.UUID,
    module: str,
    request: Request,
    current_user: User = Depends(require_permission("users.roles.assign")),
    db: AsyncSession = Depends(get_db),
):
    """Удаляет уровень доступа пользователя к указанному модулю."""
    result = await db.execute(
        select(UserModuleAccess).where(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.module == module,
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Назначение не найдено")

    old_level = existing.level
    await db.delete(existing)

    await log_action(
        db, current_user.id, "user.module_access.remove", "user", user_id,
        details={"module": module, "removed_level": old_level},
        ip_address=get_client_ip(request),
    )
    await db.commit()

    return AdminMessageResponse(message=f"Уровень доступа к модулю «{module}» удалён")
