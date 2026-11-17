"""Application settings, managed exclusively by pydantic-settings.

Every runtime value (database URL, JWT secret, CORS origins) is read from
environment variables / the local `.env` file so that no secret is ever
hard-coded into the source tree (AGENTS.md guardrail #1).
"""

from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central, typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---------------------------------------------------------
    PROJECT_NAME: str = "EcoBite - Smart Meal Management"
    API_V1_STR: str = "/api/v1"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # --- Security / JWT ------------------------------------------------------
    # openssl rand -hex 32
    SECRET_KEY: str = "CHANGE_ME_INSECURE_DEV_SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Dynamic QR Token (HMAC-SHA256, Guardrail #3) ------------------------
    # Read from environment / .env (falls back to SECRET_KEY when unset).
    QR_SIGNATURE_SECRET: str | None = None
    QR_TOKEN_VALIDITY_MINUTES: int = 60

    # --- VNPay Payment Gateway Configuration ---------------------------------
    VNP_TMN_CODE: str = ""
    VNP_HASH_SECRET: str = ""
    VNP_URL: str = ""
    VNP_RETURN_URL: str = ""

    # --- Database (async driver used by the app) ------------------------------
    # Postgres  : postgresql+asyncpg://user:pass@host:5432/db
    # Local dev : sqlite+aiosqlite:///./ecobite.db
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecobite.db"

    # --- Redis (cache & distributed locks; redis:7-alpine in docker-compose) --
    # Never hardcode host/port: everything is env-driven (AGENTS.md guardrail #1).
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT_SECONDS: float = 2.0
    REDIS_LOCK_TIMEOUT_SECONDS: int = 10

    # --- CORS -----------------------------------------------------------------
    # Accepts either a JSON array or a comma-separated string in .env.
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Split 'http://a,http://b' style strings into a list of origins."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce secure SECRET_KEY in production environments."""
        if self.APP_ENV == "production" and "CHANGE_ME" in self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be changed in production. "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return self

    @property
    def qr_signing_key(self) -> str:
        """Return the HMAC-SHA256 secret key for pickup QR tokens from settings."""
        key = self.SECRET_KEY if self.QR_SIGNATURE_SECRET is None else self.QR_SIGNATURE_SECRET
        if not key or not key.strip():
            raise ValueError("QR signing secret must be configured and non-empty")
        return key

    @property
    def sync_database_url(self) -> str:
        """Synchronous database URL for Alembic migrations (sync drivers only)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg"):
            return url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
        if url.startswith("sqlite+aiosqlite"):
            return url.replace("sqlite+aiosqlite", "sqlite", 1)
        return url


settings = Settings()
