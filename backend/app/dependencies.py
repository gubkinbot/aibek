from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
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
    """Require that user is active (not blocked)."""
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")
    return user


def _user_has_role(user: User, role_name: str) -> bool:
    return any(r.name == role_name for r in user.roles)


def _user_has_permission(user: User, codename: str) -> bool:
    """Check if user has a specific permission through roles or groups."""
    if _user_has_role(user, "superadmin"):
        return True
    for role in user.roles:
        for perm in role.permissions:
            if perm.codename == codename:
                return True
    for group in user.groups:
        for perm in group.permissions:
            if perm.codename == codename:
                return True
    return False


def require_permission(*codenames: str):
    """Dependency factory: require that user has at least one of the given permissions."""
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
    """Require superadmin role."""
    if not _user_has_role(user, "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуется роль суперадминистратора")
    return user


def get_client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
