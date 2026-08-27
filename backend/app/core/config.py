from typing import List, Union, Optional

import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

logger = logging.getLogger("datalyze.security")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Datalyze"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    
    # Secret Key loaded securely from environment variable
    SECRET_KEY: str = Field(
        default="datalyze-dev-key-change-in-production-2026-decision-intel",
        validation_alias="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database settings: Supports PostgreSQL or SQLite
    DATABASE_URL: str = Field(
        default="sqlite:///./datalyze.db",
        validation_alias="DATABASE_URL"
    )

    # CORS: Restricted strictly to trusted application origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Email Service (Resend) Settings
    RESEND_API_KEY: Optional[str] = Field(default=None, validation_alias="RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = Field(default="Datalyze <onboarding@resend.dev>", validation_alias="RESEND_FROM_EMAIL")
    FRONTEND_URL: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_URL")


    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("ENVIRONMENT", "development").lower() == "production":
            if "change-in-production" in v or len(v) < 32:
                raise ValueError("CRITICAL SECURITY ERROR: Production SECRET_KEY must be a strong random secret set via environment variable.")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()

