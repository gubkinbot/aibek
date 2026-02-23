import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_client_ip, require_permission, _user_has_role
from app.models.department import Department
from app.models.group import Group
from app.models.role import Role
from app.models.user import User
from app.schemas.admin import (
    AdminCreateUser,
    AdminMessageResponse,
    AdminUpdateUser,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserResponse,
    AssignDepartmentsRequest,
    AssignGroupsRequest,
    AssignRolesRequest,
    BlockUserRequest,
)
from app.services.audit import log_action
from app.services.auth import hash_password

router = APIRouter(prefix="/users", tags=["admin-users"])


def _serialize_user_list_item(user: User) -> AdminUserListItem:
    return AdminUserListItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        auth_provider=user.auth_provider,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        role_names=[r.name for r in user.roles],
    )


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    auth_provider: str | None = Query(None),
    current_user: User = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).options(selectinload(User.roles))

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern),
            )
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if auth_provider:
        query = query.where(User.auth_provider == auth_provider)
    if role:
        query = query.join(User.roles).where(Role.name == role)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().unique().all()

    return AdminUserListResponse(
        items=[_serialize_user_list_item(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )


@router.get("/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("", response_model=AdminMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: AdminCreateUser,
    request: Request,
    current_user: User = Depends(require_permission("users.create")),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicates
    if data.email:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    if data.phone:
        existing = await db.execute(select(User).where(User.phone == data.phone))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Пользователь с таким телефоном уже существует")

    # Generate password if not provided for email users
    temp_password = None
    hashed = None
    if data.auth_provider == "email":
        if not data.email:
            raise HTTPException(status_code=400, detail="Email обязателен для email-пользователя")
        if data.password:
            hashed = hash_password(data.password)
        else:
            temp_password = secrets.token_urlsafe(8)
            hashed = hash_password(temp_password)

    user = User(
        email=data.email,
        hashed_password=hashed,
        full_name=data.full_name,
        phone=data.phone,
        telegram_id=data.telegram_id,
        auth_provider=data.auth_provider,
        is_verified=True,  # Admin-created users are pre-verified
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    if data.role_ids:
        result = await db.execute(select(Role).where(Role.id.in_(data.role_ids)))
        roles = result.scalars().all()
        # Prevent assigning superadmin unless current user is superadmin
        for r in roles:
            if r.name == "superadmin" and not _user_has_role(current_user, "superadmin"):
                raise HTTPException(status_code=403, detail="Только суперадминистратор может назначать роль суперадмина")
        user.roles = list(roles)

    await log_action(db, current_user.id, "user.create", "user", user.id, ip_address=get_client_ip(request))
    await db.commit()

    msg = f"Пользователь {data.email or data.phone} создан"
    if temp_password:
        msg += f". Временный пароль: {temp_password}"

    return AdminMessageResponse(message=msg, temp_password=temp_password)


@router.patch("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: AdminUpdateUser,
    request: Request,
    current_user: User = Depends(require_permission("users.edit")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Cannot edit superadmin unless you are superadmin
    if _user_has_role(user, "superadmin") and not _user_has_role(current_user, "superadmin"):
        raise HTTPException(status_code=403, detail="Нельзя редактировать суперадминистратора")

    changes = {}
    if data.full_name is not None:
        changes["full_name"] = {"old": user.full_name, "new": data.full_name}
        user.full_name = data.full_name
    if data.email is not None:
        # Check uniqueness
        existing = await db.execute(select(User).where(User.email == data.email, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email уже используется")
        changes["email"] = {"old": user.email, "new": data.email}
        user.email = data.email
    if data.phone is not None:
        existing = await db.execute(select(User).where(User.phone == data.phone, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Телефон уже используется")
        changes["phone"] = {"old": user.phone, "new": data.phone}
        user.phone = data.phone

    if changes:
        await log_action(db, current_user.id, "user.edit", "user", user.id, details=changes, ip_address=get_client_ip(request))

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/block", response_model=AdminMessageResponse)
async def block_user(
    user_id: uuid.UUID,
    data: BlockUserRequest,
    request: Request,
    current_user: User = Depends(require_permission("users.block")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if _user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Нельзя заблокировать суперадминистратора")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь уже заблокирован")

    from datetime import datetime, timezone
    user.is_active = False
    user.blocked_at = datetime.now(timezone.utc)
    user.blocked_reason = data.reason

    await log_action(
        db, current_user.id, "user.block", "user", user.id,
        details={"reason": data.reason}, ip_address=get_client_ip(request),
    )
    await db.commit()
    return AdminMessageResponse(message="Пользователь заблокирован")


@router.post("/{user_id}/unblock", response_model=AdminMessageResponse)
async def unblock_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("users.block")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь не заблокирован")

    user.is_active = True
    user.blocked_at = None
    user.blocked_reason = None

    await log_action(db, current_user.id, "user.unblock", "user", user.id, ip_address=get_client_ip(request))
    await db.commit()
    return AdminMessageResponse(message="Пользователь разблокирован")


@router.post("/{user_id}/reset-password", response_model=AdminMessageResponse)
async def reset_password(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("users.reset_password")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if _user_has_role(user, "superadmin") and not _user_has_role(current_user, "superadmin"):
        raise HTTPException(status_code=403, detail="Нельзя сбросить пароль суперадминистратора")

    if user.auth_provider != "email":
        raise HTTPException(status_code=400, detail="Сброс пароля доступен только для email-пользователей")

    temp_password = secrets.token_urlsafe(8)
    user.hashed_password = hash_password(temp_password)

    await log_action(db, current_user.id, "user.reset_password", "user", user.id, ip_address=get_client_ip(request))
    await db.commit()

    # Send email with temp password if mail is enabled
    from app.config import settings
    if settings.mail_enabled and user.email:
        try:
            from app.services.email import send_password_reset_email
            await send_password_reset_email(user.email, temp_password)
        except Exception:
            pass  # Still return temp password to admin

    return AdminMessageResponse(
        message=f"Пароль сброшен для {user.email}",
        temp_password=temp_password,
    )


@router.delete("/{user_id}", response_model=AdminMessageResponse)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission("users.delete")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if _user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Нельзя удалить суперадминистратора")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")

    email = user.email or user.phone
    await log_action(db, current_user.id, "user.delete", "user", user.id,
                     details={"email": user.email, "full_name": user.full_name}, ip_address=get_client_ip(request))
    await db.delete(user)
    await db.commit()
    return AdminMessageResponse(message=f"Пользователь {email} удалён")


@router.put("/{user_id}/roles", response_model=AdminUserResponse)
async def assign_roles(
    user_id: uuid.UUID,
    data: AssignRolesRequest,
    request: Request,
    current_user: User = Depends(require_permission("roles.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    result = await db.execute(select(Role).where(Role.id.in_(data.role_ids)))
    new_roles = result.scalars().all()

    # Prevent non-superadmin from assigning/removing superadmin role
    for r in new_roles:
        if r.name == "superadmin" and not _user_has_role(current_user, "superadmin"):
            raise HTTPException(status_code=403, detail="Только суперадминистратор может назначать роль суперадмина")

    old_role_names = [r.name for r in user.roles]
    user.roles = list(new_roles)
    new_role_names = [r.name for r in new_roles]

    await log_action(
        db, current_user.id, "user.roles.assign", "user", user.id,
        details={"old": old_role_names, "new": new_role_names},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/groups", response_model=AdminUserResponse)
async def assign_groups(
    user_id: uuid.UUID,
    data: AssignGroupsRequest,
    request: Request,
    current_user: User = Depends(require_permission("groups.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    result = await db.execute(select(Group).where(Group.id.in_(data.group_ids)))
    new_groups = result.scalars().all()

    old_names = [g.name for g in user.groups]
    user.groups = list(new_groups)
    new_names = [g.name for g in new_groups]

    await log_action(
        db, current_user.id, "user.groups.assign", "user", user.id,
        details={"old": old_names, "new": new_names},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/departments", response_model=AdminUserResponse)
async def assign_departments(
    user_id: uuid.UUID,
    data: AssignDepartmentsRequest,
    request: Request,
    current_user: User = Depends(require_permission("departments.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    result = await db.execute(select(Department).where(Department.id.in_(data.department_ids)))
    new_depts = result.scalars().all()

    old_names = [d.name for d in user.departments]
    user.departments = list(new_depts)
    new_names = [d.name for d in new_depts]

    await log_action(
        db, current_user.id, "user.departments.assign", "user", user.id,
        details={"old": old_names, "new": new_names},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return user
