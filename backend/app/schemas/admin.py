import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ── Pagination ──────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


# ── Permission ──────────────────────────────────────────────

class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    display_name: str
    category: str

    class Config:
        from_attributes = True


class PermissionsByCategory(BaseModel):
    category: str
    permissions: list[PermissionResponse]


# ── Role ────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or len(v) < 2:
            raise ValueError("Название роли должно быть не менее 2 символов")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Название роли может содержать только буквы, цифры, _ и -")
        return v


class RoleUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str | None
    is_system: bool
    created_at: datetime
    user_count: int = 0

    class Config:
        from_attributes = True


class RoleDetailResponse(RoleResponse):
    permissions: list[PermissionResponse]


class SetRolePermissionsRequest(BaseModel):
    permission_ids: list[uuid.UUID]


# ── Group ───────────────────────────────────────────────────

class GroupCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("Название группы должно быть не менее 2 символов")
        return v


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    user_count: int = 0
    permission_count: int = 0

    class Config:
        from_attributes = True


class GroupDetailResponse(GroupResponse):
    permissions: list[PermissionResponse]


class SetGroupPermissionsRequest(BaseModel):
    permission_ids: list[uuid.UUID]


class SetGroupMembersRequest(BaseModel):
    user_ids: list[uuid.UUID]


# ── Department ──────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("Название подразделения должно быть не менее 2 символов")
        return v


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: uuid.UUID | None = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    parent_id: uuid.UUID | None
    created_at: datetime
    user_count: int = 0

    class Config:
        from_attributes = True


class DepartmentTreeResponse(DepartmentResponse):
    children: list["DepartmentTreeResponse"] = []


# ── Admin User Management ──────────────────────────────────

class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    telegram_id: int | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    blocked_at: datetime | None
    blocked_reason: str | None
    created_at: datetime
    updated_at: datetime | None
    roles: list[RoleResponse] = []
    groups: list[GroupResponse] = []
    departments: list[DepartmentResponse] = []

    class Config:
        from_attributes = True


class AdminUserListItem(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    role_names: list[str] = []

    class Config:
        from_attributes = True


class AdminUserListResponse(PaginatedResponse):
    items: list[AdminUserListItem]


class AdminCreateUser(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    phone: str | None = None
    telegram_id: int | None = None
    auth_provider: str = "email"
    role_ids: list[uuid.UUID] = []

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class AdminUpdateUser(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class BlockUserRequest(BaseModel):
    reason: str | None = None


class AssignRolesRequest(BaseModel):
    role_ids: list[uuid.UUID]


class AssignGroupsRequest(BaseModel):
    group_ids: list[uuid.UUID]


class AssignDepartmentsRequest(BaseModel):
    department_ids: list[uuid.UUID]


# ── Audit Log ──────────────────────────────────────────────

class AuditLogResponse(BaseModel):
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
    items: list[AuditLogResponse]


# ── Message ────────────────────────────────────────────────

class AdminMessageResponse(BaseModel):
    message: str
    temp_password: str | None = None
