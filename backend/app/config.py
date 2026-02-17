from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
