from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    rate_limit_per_minute: int = 30
    login_rate_limit_per_minute: int = 5
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(repr=False)
    app_name: str = "Pulse API"
    version: str = "1.0.0"
    db_echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    cors_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]
    jwt_secret: str = Field(min_length=32, repr=False)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    @field_validator("database_url")
    @classmethod
    def async_postgres(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL debe empezar con postgresql+asyncpg://")
        return value


settings = Settings()

