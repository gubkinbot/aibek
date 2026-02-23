"""Настройки приложения, загружаемые из переменных окружения (.env)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация приложения (Pydantic Settings)."""

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    redis_url: str = "redis://redis:6379/0"

    # Mail (SMTP relay)
    mail_smtp_host: str = "10.1.10.13"
    mail_smtp_port: int = 25
    mail_from: str = "ai@utg.uz"
    mail_enabled: bool = True  # False = dev mode, code goes to console

    # Verification
    verification_code_ttl: int = 600  # 10 minutes in seconds

    # Superadmin
    superadmin_email: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
