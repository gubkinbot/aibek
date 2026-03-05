"""Определение уровней доступа к модулям и управление доступом по умолчанию.

Каждый модуль имеет список именованных уровней доступа.
Каждый уровень соответствует фиксированному набору permissions.
Уровни определены в коде (не в БД), так как тесно связаны с permissions.

Также содержит функции для работы с доступом по умолчанию
(автоматически назначаемым новым пользователям при верификации email)."""

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module_access import UserModuleAccess
from app.services.redis import redis_client


def _module_levels(module: str) -> list[dict]:
    """Генерирует стандартные 4 уровня доступа для проектного модуля."""
    return [
        {
            "level": "viewer",
            "display_name": "Наблюдатель",
            "description": "Только просмотр данных",
            "permissions": [
                f"{module}.access",
                f"{module}.view",
            ],
        },
        {
            "level": "operator",
            "display_name": "Оператор",
            "description": "Просмотр и работа с данными",
            "permissions": [
                f"{module}.access",
                f"{module}.view",
                f"{module}.edit",
            ],
        },
        {
            "level": "manager",
            "display_name": "Руководитель",
            "description": "Полное управление модулем",
            "permissions": [
                f"{module}.access",
                f"{module}.view",
                f"{module}.edit",
                f"{module}.manage",
            ],
        },
        {
            "level": "admin",
            "display_name": "Администратор",
            "description": "Администрирование модуля и настройки",
            "permissions": [
                f"{module}.access",
                f"{module}.view",
                f"{module}.edit",
                f"{module}.manage",
                f"{module}.admin",
            ],
        },
    ]


MODULE_ACCESS_LEVELS: dict[str, list[dict]] = {
    "admin": [
        {
            "level": "viewer",
            "display_name": "Наблюдатель",
            "description": "Просмотр пользователей и журнала действий",
            "permissions": [
                "users.view",
                "audit.view",
            ],
        },
        {
            "level": "operator",
            "display_name": "Оператор",
            "description": "Управление пользователями: создание, блокировка, сброс пароля",
            "permissions": [
                "users.view",
                "users.create",
                "users.edit",
                "users.delete",
                "users.block",
                "users.reset_password",
                "audit.view",
            ],
        },
        {
            "level": "manager",
            "display_name": "Руководитель",
            "description": "Полное управление пользователями",
            "permissions": [
                "users.view",
                "users.create",
                "users.edit",
                "users.delete",
                "users.block",
                "users.reset_password",
                "audit.view",
            ],
        },
        {
            "level": "admin",
            "display_name": "Администратор",
            "description": "Полный доступ к модулю администрирования",
            "permissions": [
                "users.view",
                "users.create",
                "users.edit",
                "users.delete",
                "users.block",
                "users.reset_password",
                "audit.view",
                "system.view",
                "system.manage",
            ],
        },
    ],
    "compressor": _module_levels("compressor"),
    "balance": _module_levels("balance"),
    "weather": _module_levels("weather"),
    "digital": _module_levels("digital"),
    "ai_chat": _module_levels("ai_chat"),
}


def get_permissions_for_module_level(module: str, level: str) -> set[str]:
    """Возвращает набор codename-ов permissions для заданной пары (модуль, уровень)."""
    levels = MODULE_ACCESS_LEVELS.get(module, [])
    for lvl in levels:
        if lvl["level"] == level:
            return set(lvl["permissions"])
    return set()


def get_valid_levels(module: str) -> list[str]:
    """Возвращает допустимые имена уровней для модуля."""
    levels = MODULE_ACCESS_LEVELS.get(module, [])
    return [lvl["level"] for lvl in levels]


def get_valid_modules() -> list[str]:
    """Возвращает список допустимых имён модулей."""
    return list(MODULE_ACCESS_LEVELS.keys())


# ── Доступ по умолчанию ───────────────────────────────────

DEFAULT_ACCESS_KEY = "default_access"


async def get_default_access() -> dict[str, str]:
    """Возвращает словарь {module: level} настроек доступа по умолчанию."""
    raw = await redis_client.get(DEFAULT_ACCESS_KEY)
    if raw:
        return json.loads(raw)
    return {}


async def set_default_access(defaults: dict[str, str]) -> None:
    """Сохраняет настройки доступа по умолчанию в Redis."""
    await redis_client.set(DEFAULT_ACCESS_KEY, json.dumps(defaults))


async def apply_default_access(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Создаёт записи UserModuleAccess по настройкам по умолчанию для нового пользователя."""
    defaults = await get_default_access()
    for module, level in defaults.items():
        access = UserModuleAccess(user_id=user_id, module=module, level=level)
        db.add(access)
    if defaults:
        await db.commit()
