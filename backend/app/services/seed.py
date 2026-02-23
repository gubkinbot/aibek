"""Инициализация данных при запуске: создание permissions и назначение суперадмина."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.permission import Permission

logger = logging.getLogger(__name__)

PERMISSIONS = [
    {"codename": "users.view", "display_name": "Просмотр пользователей", "category": "users"},
    {"codename": "users.create", "display_name": "Создание пользователей", "category": "users"},
    {"codename": "users.edit", "display_name": "Редактирование пользователей", "category": "users"},
    {"codename": "users.delete", "display_name": "Удаление пользователей", "category": "users"},
    {"codename": "users.block", "display_name": "Блокировка пользователей", "category": "users"},
    {"codename": "users.reset_password", "display_name": "Сброс пароля", "category": "users"},
    {"codename": "audit.view", "display_name": "Просмотр журнала действий", "category": "audit"},
    {"codename": "system.view", "display_name": "Просмотр мониторинга системы", "category": "system"},
    {"codename": "system.manage", "display_name": "Управление системой", "category": "system"},
    # Module: Compressor
    {"codename": "compressor.access", "display_name": "Доступ к модулю «Компрессорные станции»", "category": "compressor"},
    {"codename": "compressor.view", "display_name": "Просмотр данных компрессорных станций", "category": "compressor"},
    {"codename": "compressor.edit", "display_name": "Редактирование данных компрессорных станций", "category": "compressor"},
    {"codename": "compressor.manage", "display_name": "Управление компрессорными станциями", "category": "compressor"},
    {"codename": "compressor.admin", "display_name": "Администрирование модуля компрессорных станций", "category": "compressor"},
    # Module: Balance
    {"codename": "balance.access", "display_name": "Доступ к модулю «Балансировка ГТС»", "category": "balance"},
    {"codename": "balance.view", "display_name": "Просмотр данных балансировки", "category": "balance"},
    {"codename": "balance.edit", "display_name": "Редактирование данных балансировки", "category": "balance"},
    {"codename": "balance.manage", "display_name": "Управление балансировкой ГТС", "category": "balance"},
    {"codename": "balance.admin", "display_name": "Администрирование модуля балансировки", "category": "balance"},
    # Module: Weather
    {"codename": "weather.access", "display_name": "Доступ к модулю «Погодные риски»", "category": "weather"},
    {"codename": "weather.view", "display_name": "Просмотр погодных данных", "category": "weather"},
    {"codename": "weather.edit", "display_name": "Редактирование погодных данных", "category": "weather"},
    {"codename": "weather.manage", "display_name": "Управление модулем погодных рисков", "category": "weather"},
    {"codename": "weather.admin", "display_name": "Администрирование модуля погодных рисков", "category": "weather"},
    # Module: Digital
    {"codename": "digital.access", "display_name": "Доступ к модулю «Цифровой департамент»", "category": "digital"},
    {"codename": "digital.view", "display_name": "Просмотр данных цифрового департамента", "category": "digital"},
    {"codename": "digital.edit", "display_name": "Редактирование данных цифрового департамента", "category": "digital"},
    {"codename": "digital.manage", "display_name": "Управление цифровым департаментом", "category": "digital"},
    {"codename": "digital.admin", "display_name": "Администрирование модуля цифрового департамента", "category": "digital"},
    # Module: AI Chat
    {"codename": "ai_chat.access", "display_name": "Доступ к модулю «ИИ-чат»", "category": "ai_chat"},
    {"codename": "ai_chat.view", "display_name": "Просмотр данных ИИ-чата", "category": "ai_chat"},
    {"codename": "ai_chat.edit", "display_name": "Редактирование данных ИИ-чата", "category": "ai_chat"},
    {"codename": "ai_chat.manage", "display_name": "Управление модулем ИИ-чата", "category": "ai_chat"},
    {"codename": "ai_chat.admin", "display_name": "Администрирование модуля ИИ-чата", "category": "ai_chat"},
    # Module: SCADA
    {"codename": "scada.access", "display_name": "Доступ к модулю «SCADA»", "category": "scada"},
    {"codename": "scada.view", "display_name": "Просмотр данных SCADA", "category": "scada"},
    {"codename": "scada.edit", "display_name": "Редактирование данных SCADA", "category": "scada"},
    {"codename": "scada.manage", "display_name": "Управление модулем SCADA", "category": "scada"},
    {"codename": "scada.admin", "display_name": "Администрирование модуля SCADA", "category": "scada"},
]


async def seed_permissions(db: AsyncSession) -> None:
    """Создаёт системные permissions в БД (идемпотентно)."""
    for perm_data in PERMISSIONS:
        result = await db.execute(select(Permission).where(Permission.codename == perm_data["codename"]))
        if not result.scalar_one_or_none():
            db.add(Permission(**perm_data))
            logger.info("Created permission: %s", perm_data["codename"])

    await db.commit()


async def ensure_superadmin(db: AsyncSession) -> None:
    """Устанавливает флаг is_superadmin для пользователя с SUPERADMIN_EMAIL."""
    if not settings.superadmin_email:
        return

    from app.models.user import User

    result = await db.execute(select(User).where(User.email == settings.superadmin_email))
    user = result.scalar_one_or_none()

    if not user or not user.is_verified:
        return

    if not user.is_superadmin:
        user.is_superadmin = True
        await db.commit()
        logger.info("Set superadmin flag for %s", settings.superadmin_email)
