"""Сервис верификации: генерация, хранение и проверка кодов подтверждения через Redis."""
import secrets

from app.config import settings
from app.services.redis import redis_client


def generate_verification_code() -> str:
    """Генерирует случайный 6-значный код подтверждения."""
    return f"{secrets.randbelow(1000000):06d}"


async def store_verification_code(email: str, code: str, prefix: str = "verify") -> None:
    """Сохраняет код подтверждения в Redis с TTL."""
    key = f"{prefix}:{email}"
    await redis_client.setex(key, settings.verification_code_ttl, code)


async def verify_code(email: str, code: str, prefix: str = "verify") -> bool:
    """Проверяет код подтверждения. При успехе удаляет код из Redis."""
    key = f"{prefix}:{email}"
    stored_code = await redis_client.get(key)
    if stored_code is None or stored_code != code:
        return False
    await redis_client.delete(key)
    return True


async def has_recent_code(email: str, prefix: str = "verify") -> bool:
    """Проверяет, был ли недавно отправлен код (защита от частых запросов)."""
    key = f"{prefix}:{email}"
    ttl = await redis_client.ttl(key)
    return ttl > (settings.verification_code_ttl - 60)
