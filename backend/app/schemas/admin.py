"""Pydantic-схемы для админ-панели: пользователи, permissions, аудит."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ── Pagination ──────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    """Базовая схема пагинированного ответа."""
    total: int
    page: int
    per_page: int
    pages: int


# ── Permission ──────────────────────────────────────────────

class PermissionResponse(BaseModel):
    """Ответ с данными permission."""
    id: uuid.UUID
    codename: str
    display_name: str
    category: str

    class Config:
        from_attributes = True


class PermissionsByCategory(BaseModel):
    """Группировка permissions по категории."""
    category: str
    permissions: list[PermissionResponse]


# ── Admin User Management ──────────────────────────────────

class AdminUserResponse(BaseModel):
    """Полный ответ с данными пользователя для админ-панели."""
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    telegram_id: int | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    is_superadmin: bool
    blocked_at: datetime | None
    blocked_reason: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class AdminUserListItem(BaseModel):
    """Краткие данные пользователя для списка."""
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    is_superadmin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(PaginatedResponse):
    """Пагинированный список пользователей."""
    items: list[AdminUserListItem]


class AdminCreateUser(BaseModel):
    """Схема создания пользователя администратором."""
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    phone: str | None = None
    telegram_id: int | None = None
    auth_provider: str = "email"
    module_access: dict[str, str] = {}  # {"compressor": "viewer", "admin": "operator"}

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str | None) -> str | None:
        """Проверяет минимальную длину пароля (6 символов)."""
        if v is not None and len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class AdminUpdateUser(BaseModel):
    """Схема редактирования пользователя."""
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class BlockUserRequest(BaseModel):
    """Запрос блокировки пользователя с причиной."""
    reason: str | None = None


# ── Module Access ─────────────────────────────────

class SetModuleAccessRequest(BaseModel):
    """Запрос назначения уровня доступа к модулю."""
    module: str
    level: str


# ── Default Access ────────────────────────────────

class DefaultAccessResponse(BaseModel):
    """Ответ с настройками доступа по умолчанию и доступными модулями/уровнями."""
    defaults: dict[str, str]
    available_modules: list[str]
    available_levels: list[str]


class DefaultAccessUpdate(BaseModel):
    """Запрос обновления настроек доступа по умолчанию."""
    defaults: dict[str, str]


# ── Audit Log ──────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    """Запись журнала аудита."""
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_name: str | None = None
    action: str
    target_type: str
    target_id: uuid.UUID
    details: dict | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(PaginatedResponse):
    """Пагинированный список записей аудита."""
    items: list[AuditLogResponse]


# ── Message ────────────────────────────────────────────────

class AdminMessageResponse(BaseModel):
    """Ответ с сообщением и опциональным временным паролем."""
    message: str
    temp_password: str | None = None
