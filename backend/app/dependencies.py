"""FastAPI-зависимости: аутентификация, проверка прав, извлечение IP."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token
from app.services.module_access import get_permissions_for_module_level

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Извлекает текущего пользователя из JWT-токена."""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Проверяет, что пользователь активен (не заблокирован)."""
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")
    return user


def _user_has_permission(user: User, codename: str) -> bool:
    """Проверяет наличие permission у пользователя через уровни доступа к модулям."""
    if user.is_superadmin:
        return True
    for ma in user.module_access:
        if codename in get_permissions_for_module_level(ma.module, ma.level):
            return True
    return False


def get_user_permissions(user: User) -> list[str]:
    """Собирает все codename-ы permissions пользователя из его уровней доступа к модулям."""
    perms: set[str] = set()
    for ma in user.module_access:
        perms.update(get_permissions_for_module_level(ma.module, ma.level))
    return sorted(perms)


def require_permission(*codenames: str):
    """Фабрика зависимостей: требует хотя бы один из указанных permissions у пользователя."""
    async def checker(user: User = Depends(get_current_active_user)) -> User:
        for codename in codenames:
            if _user_has_permission(user, codename):
                return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения этого действия",
        )
    return checker


async def get_current_superadmin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Требует флаг суперадминистратора у текущего пользователя."""
    if not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуется роль суперадминистратора")
    return user


def get_client_ip(request: Request) -> str | None:
    """Извлекает IP-адрес клиента из заголовков запроса (X-Forwarded-For или client.host)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
