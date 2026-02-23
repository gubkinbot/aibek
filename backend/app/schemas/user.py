"""Pydantic-схемы для аутентификации и профиля пользователя."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Схема регистрации: email, пароль, ФИО."""
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_corporate(cls, v: str) -> str:
        """Проверяет, что email принадлежит домену @utg.uz."""
        if not v.endswith("@utg.uz"):
            raise ValueError("Разрешена регистрация только с корпоративной почтой @utg.uz")
        return v.lower()


class UserLogin(BaseModel):
    """Схема входа: email и пароль."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Ответ с данными пользователя (профиль, permissions, уровни доступа)."""
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    is_superadmin: bool = False
    permissions: list[str] = []
    module_access: dict[str, str] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT-токен доступа."""
    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    """Запрос подтверждения email: email и 6-значный код."""
    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def code_must_be_six_digits(cls, v: str) -> str:
        """Проверяет, что код состоит из 6 цифр."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Код должен состоять из 6 цифр")
        return v


class ResendCodeRequest(BaseModel):
    """Запрос повторной отправки кода подтверждения."""
    email: EmailStr


class MessageResponse(BaseModel):
    """Стандартный ответ с текстовым сообщением."""
    message: str


class ForgotPasswordRequest(BaseModel):
    """Запрос сброса пароля: email."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Запрос сброса пароля: email, код и новый пароль."""
    email: EmailStr
    code: str
    new_password: str

    @field_validator("code")
    @classmethod
    def code_must_be_six_digits(cls, v: str) -> str:
        """Проверяет, что код состоит из 6 цифр."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Код должен состоять из 6 цифр")
        return v

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Проверяет минимальную длину пароля (6 символов)."""
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class ChangePasswordRequest(BaseModel):
    """Запрос смены пароля: текущий и новый пароль."""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Проверяет минимальную длину пароля (6 символов)."""
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class UpdateProfileRequest(BaseModel):
    """Запрос обновления профиля."""
    full_name: str | None = None
