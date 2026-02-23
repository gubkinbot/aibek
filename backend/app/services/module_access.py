"""Определение уровней доступа к модулям.

Каждый модуль имеет список именованных уровней доступа.
Каждый уровень соответствует фиксированному набору permissions.
Уровни определены в коде (не в БД), так как тесно связаны с permissions."""


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
    "scada": _module_levels("scada"),
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
