"""Regression tests for production deployment settings."""

import pytest
from pydantic import ValidationError

from backend.app.config import Settings


def test_neon_url_selects_psycopg3() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:secret@example.neon.tech/navalforge?sslmode=require",
    )

    assert settings.sqlalchemy_database_url == (
        "postgresql+psycopg://user:secret@example.neon.tech/navalforge?sslmode=require"
    )


def test_cors_origins_are_normalized_and_deduplicated() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins=(
            "https://navalforge3d14.pages.dev/, https://navalforge3d14.pages.dev"
        ),
    )

    assert settings.cors_origin_list == ["https://navalforge3d14.pages.dev"]


def test_production_always_trusts_the_published_pwa_origins() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        database_url="postgresql://user:secret@example.neon.tech/navalforge",
        cors_origins="https://navalforge3d14.pages.dev",
    )

    assert settings.cors_origin_list == [
        "https://navalforge3d14.pages.dev",
        "https://navalforgeconcept.pages.dev",
    ]


def test_production_rejects_ephemeral_sqlite() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL DATABASE_URL"):
        Settings(
            _env_file=None,
            environment="production",
            database_url="sqlite:///./navalforge.db",
            cors_origins="https://navalforge3d14.pages.dev",
        )


def test_production_rejects_insecure_cors() -> None:
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(
            _env_file=None,
            environment="production",
            database_url="postgresql://user:secret@example.neon.tech/navalforge",
            cors_origins="http://navalforge.example",
        )
