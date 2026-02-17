import secrets

from app.config import settings
from app.services.redis import redis_client


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


async def store_verification_code(email: str, code: str, prefix: str = "verify") -> None:
    key = f"{prefix}:{email}"
    await redis_client.setex(key, settings.verification_code_ttl, code)


async def verify_code(email: str, code: str, prefix: str = "verify") -> bool:
    key = f"{prefix}:{email}"
    stored_code = await redis_client.get(key)
    if stored_code is None or stored_code != code:
        return False
    await redis_client.delete(key)
    return True


async def has_recent_code(email: str, prefix: str = "verify") -> bool:
    key = f"{prefix}:{email}"
    ttl = await redis_client.ttl(key)
    return ttl > (settings.verification_code_ttl - 60)
