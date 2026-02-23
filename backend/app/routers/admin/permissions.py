from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.models.permission import Permission
from app.models.user import User
from app.schemas.admin import PermissionResponse, PermissionsByCategory

router = APIRouter(prefix="/permissions", tags=["admin-permissions"])


@router.get("", response_model=list[PermissionsByCategory])
async def list_permissions(
    current_user: User = Depends(require_permission("roles.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Permission).order_by(Permission.category, Permission.codename))
    perms = result.scalars().all()

    categories: dict[str, list[PermissionResponse]] = {}
    for p in perms:
        pr = PermissionResponse(id=p.id, codename=p.codename, display_name=p.display_name, category=p.category)
        categories.setdefault(p.category, []).append(pr)

    return [PermissionsByCategory(category=cat, permissions=items) for cat, items in categories.items()]
