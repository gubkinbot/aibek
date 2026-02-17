import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_corporate(cls, v: str) -> str:
        if not v.endswith("@utg.uz"):
            raise ValueError("Разрешена регистрация только с корпоративной почтой @utg.uz")
        return v.lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def code_must_be_six_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Код должен состоять из 6 цифр")
        return v


class ResendCodeRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str
