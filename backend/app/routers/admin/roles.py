import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_client_ip, require_permission
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.admin import (
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
    SetRolePermissionsRequest,
)
from app.services.audit import log_action

router = APIRouter(prefix="/roles", tags=["admin-roles"])


def _role_to_response(role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        user_count=len(role.users),
    )


@router.get("/", response_model=list[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_permission("roles.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).order_by(Role.is_system.desc(), Role.name))
    roles = result.scalars().unique().all()
    return [_role_to_response(r) for r in roles]


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    request: Request,
    current_user: User = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Роль с таким именем уже существует")

    role = Role(name=data.name, display_name=data.display_name, description=data.description)
    db.add(role)
    await db.flush()

    await log_action(db, current_user.id, "role.create", "role", role.id, ip_address=get_client_ip(request))
    await db.commit()
    await db.refresh(role)
    return _role_to_response(role)


@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: uuid.UUID,
    current_user: User = Depends(require_permission("roles.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    return RoleDetailResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        user_count=len(role.users),
        permissions=role.permissions,
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    data: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    if role.is_system:
        raise HTTPException(status_code=403, detail="Системные роли нельзя редактировать")

    changes = {}
    if data.display_name is not None:
        changes["display_name"] = {"old": role.display_name, "new": data.display_name}
        role.display_name = data.display_name
    if data.description is not None:
        changes["description"] = {"old": role.description, "new": data.description}
        role.description = data.description

    if changes:
        await log_action(db, current_user.id, "role.edit", "role", role.id, details=changes, ip_address=get_client_ip(request))

    await db.commit()
    await db.refresh(role)
    return _role_to_response(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    if role.is_system:
        raise HTTPException(status_code=403, detail="Системные роли нельзя удалять")

    if role.users:
        raise HTTPException(status_code=400, detail="Нельзя удалить роль, назначенную пользователям")

    await log_action(
        db, current_user.id, "role.delete", "role", role.id,
        details={"name": role.name}, ip_address=get_client_ip(request),
    )
    await db.delete(role)
    await db.commit()
    return {"message": f"Роль «{role.display_name}» удалена"}


@router.put("/{role_id}/permissions", response_model=RoleDetailResponse)
async def set_role_permissions(
    role_id: uuid.UUID,
    data: SetRolePermissionsRequest,
    request: Request,
    current_user: User = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    if role.name == "superadmin":
        raise HTTPException(status_code=403, detail="Суперадминистратор имеет все права автоматически")

    result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
    new_perms = result.scalars().all()

    old_codenames = [p.codename for p in role.permissions]
    role.permissions = list(new_perms)
    new_codenames = [p.codename for p in new_perms]

    await log_action(
        db, current_user.id, "role.permissions.set", "role", role.id,
        details={"old": old_codenames, "new": new_codenames},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(role)

    return RoleDetailResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        user_count=len(role.users),
        permissions=role.permissions,
    )
