import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_client_ip, require_permission
from app.models.group import Group
from app.models.permission import Permission
from app.models.user import User
from app.schemas.admin import (
    GroupCreate,
    GroupDetailResponse,
    GroupResponse,
    GroupUpdate,
    SetGroupMembersRequest,
    SetGroupPermissionsRequest,
)
from app.services.audit import log_action

router = APIRouter(prefix="/groups", tags=["admin-groups"])


def _group_to_response(group: Group) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        user_count=len(group.users),
        permission_count=len(group.permissions),
    )


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    current_user: User = Depends(require_permission("groups.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().unique().all()
    return [_group_to_response(g) for g in groups]


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Group).where(Group.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Группа с таким именем уже существует")

    group = Group(name=data.name, description=data.description)
    db.add(group)
    await db.flush()

    await log_action(db, current_user.id, "group.create", "group", group.id, ip_address=get_client_ip(request))
    await db.commit()
    await db.refresh(group)
    return _group_to_response(group)


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(require_permission("groups.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        user_count=len(group.users),
        permission_count=len(group.permissions),
        permissions=group.permissions,
    )


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    changes = {}
    if data.name is not None:
        existing = await db.execute(select(Group).where(Group.name == data.name, Group.id != group_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Группа с таким именем уже существует")
        changes["name"] = {"old": group.name, "new": data.name}
        group.name = data.name
    if data.description is not None:
        changes["description"] = {"old": group.description, "new": data.description}
        group.description = data.description

    if changes:
        await log_action(db, current_user.id, "group.edit", "group", group.id, details=changes, ip_address=get_client_ip(request))

    await db.commit()
    await db.refresh(group)
    return _group_to_response(group)


@router.delete("/{group_id}")
async def delete_group(
    group_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    if group.users:
        raise HTTPException(status_code=400, detail="Нельзя удалить группу с участниками. Сначала уберите всех пользователей.")

    await log_action(
        db, current_user.id, "group.delete", "group", group.id,
        details={"name": group.name}, ip_address=get_client_ip(request),
    )
    await db.delete(group)
    await db.commit()
    return {"message": f"Группа «{group.name}» удалена"}


@router.put("/{group_id}/permissions", response_model=GroupDetailResponse)
async def set_group_permissions(
    group_id: uuid.UUID,
    data: SetGroupPermissionsRequest,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
    new_perms = result.scalars().all()

    old_codenames = [p.codename for p in group.permissions]
    group.permissions = list(new_perms)
    new_codenames = [p.codename for p in new_perms]

    await log_action(
        db, current_user.id, "group.permissions.set", "group", group.id,
        details={"old": old_codenames, "new": new_codenames},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(group)

    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        user_count=len(group.users),
        permission_count=len(group.permissions),
        permissions=group.permissions,
    )


@router.put("/{group_id}/members", response_model=GroupDetailResponse)
async def set_group_members(
    group_id: uuid.UUID,
    data: SetGroupMembersRequest,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    result = await db.execute(select(User).where(User.id.in_(data.user_ids)))
    new_members = result.scalars().unique().all()

    old_ids = [str(u.id) for u in group.users]
    group.users = list(new_members)
    new_ids = [str(u.id) for u in new_members]

    await log_action(
        db, current_user.id, "group.members.set", "group", group.id,
        details={"old_count": len(old_ids), "new_count": len(new_ids)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(group)

    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        user_count=len(group.users),
        permission_count=len(group.permissions),
        permissions=group.permissions,
    )
