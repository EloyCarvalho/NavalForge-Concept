"""Environment-driven API configuration."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NavalForge Concept API"
    app_version: str = "0.1.6"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./navalforge.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: str = "storage"
    celery_enabled: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    max_variants: int = Field(default=81, ge=1, le=10000)

    @property
    def cors_origin_list(self) -> list[str]:
        origins: list[str] = []
        for item in self.cors_origins.split(","):
            origin = item.strip().rstrip("/")
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a SQLAlchemy URL that explicitly selects psycopg 3.

        Neon and several other managed PostgreSQL providers expose a standard
        ``postgresql://`` (or legacy ``postgres://``) connection string.
        SQLAlchemy otherwise attempts to import psycopg2, while NavalForge
        deliberately ships with psycopg 3.
        """

        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Fail fast instead of silently using ephemeral SQLite in production."""

        if self.environment.strip().lower() not in {"production", "prod"}:
            return self
        if not self.sqlalchemy_database_url.startswith("postgresql+psycopg://"):
            raise ValueError("Production requires a PostgreSQL DATABASE_URL")
        origins = self.cors_origin_list
        if not origins or "*" in origins:
            raise ValueError("Production requires explicit HTTPS CORS_ORIGINS")
        if any(not origin.startswith("https://") for origin in origins):
            raise ValueError("Production CORS_ORIGINS must use HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
