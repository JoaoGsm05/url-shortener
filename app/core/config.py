from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    base_url: str = "http://localhost:8000"
    environment: str = "development"
    slug_length: int = 7

    @field_validator("database_url", mode="before")
    @classmethod
    def normalizar_url_postgres(cls, v: str) -> str:
        # Render entrega postgresql:// ou postgres://; asyncpg exige postgresql+asyncpg://
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg2")


settings = Settings()
