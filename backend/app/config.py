"""Environment-driven API configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NavalForge Concept API"
    app_version: str = "0.1.5"
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
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
