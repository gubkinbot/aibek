import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.permission import Permission
from app.models.role import Role
from app.models.associations import role_permissions, user_roles

logger = logging.getLogger(__name__)

SYSTEM_ROLES = [
    {"name": "superadmin", "display_name": "Суперадминистратор", "description": "Полный доступ ко всем функциям платформы", "is_system": True},
    {"name": "admin", "display_name": "Администратор", "description": "Управление пользователями и настройками", "is_system": True},
    {"name": "user", "display_name": "Пользователь", "description": "Базовый доступ к платформе", "is_system": True},
]

PERMISSIONS = [
    {"codename": "users.view", "display_name": "Просмотр пользователей", "category": "users"},
    {"codename": "users.create", "display_name": "Создание пользователей", "category": "users"},
    {"codename": "users.edit", "display_name": "Редактирование пользователей", "category": "users"},
    {"codename": "users.delete", "display_name": "Удаление пользователей", "category": "users"},
    {"codename": "users.block", "display_name": "Блокировка пользователей", "category": "users"},
    {"codename": "users.reset_password", "display_name": "Сброс пароля", "category": "users"},
    {"codename": "roles.view", "display_name": "Просмотр ролей", "category": "roles"},
    {"codename": "roles.manage", "display_name": "Управление ролями", "category": "roles"},
    {"codename": "groups.view", "display_name": "Просмотр групп", "category": "groups"},
    {"codename": "groups.manage", "display_name": "Управление группами", "category": "groups"},
    {"codename": "departments.view", "display_name": "Просмотр подразделений", "category": "departments"},
    {"codename": "departments.manage", "display_name": "Управление подразделениями", "category": "departments"},
    {"codename": "audit.view", "display_name": "Просмотр журнала действий", "category": "audit"},
]

# Permissions assigned to admin role (everything except roles.manage)
ADMIN_PERMISSIONS = [p["codename"] for p in PERMISSIONS if p["codename"] != "roles.manage"]


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """Seed system roles and permissions on startup."""
    # Seed permissions
    for perm_data in PERMISSIONS:
        result = await db.execute(select(Permission).where(Permission.codename == perm_data["codename"]))
        if not result.scalar_one_or_none():
            db.add(Permission(**perm_data))
            logger.info("Created permission: %s", perm_data["codename"])

    await db.flush()

    # Seed roles
    for role_data in SYSTEM_ROLES:
        result = await db.execute(select(Role).where(Role.name == role_data["name"]))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(**role_data)
            db.add(role)
            logger.info("Created system role: %s", role_data["name"])

    await db.flush()

    # Assign permissions to admin role
    result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    if admin_role and not admin_role.permissions:
        result = await db.execute(select(Permission).where(Permission.codename.in_(ADMIN_PERMISSIONS)))
        perms = result.scalars().all()
        admin_role.permissions = list(perms)
        logger.info("Assigned %d permissions to admin role", len(perms))

    await db.commit()


async def ensure_superadmin(db: AsyncSession) -> None:
    """If SUPERADMIN_EMAIL is set, ensure that user has superadmin role."""
    if not settings.superadmin_email:
        return

    from app.models.user import User

    result = await db.execute(select(User).where(User.email == settings.superadmin_email))
    user = result.scalar_one_or_none()

    if not user or not user.is_verified:
        return

    result = await db.execute(select(Role).where(Role.name == "superadmin"))
    superadmin_role = result.scalar_one_or_none()
    if not superadmin_role:
        return

    if superadmin_role not in user.roles:
        user.roles.append(superadmin_role)
        await db.commit()
        logger.info("Assigned superadmin role to %s", settings.superadmin_email)
