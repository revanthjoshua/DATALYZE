from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Datalyze"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "datalyze-super-secret-key-change-in-production-2026-decision-intel"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for dev/MVP

    # Database settings: Supports PostgreSQL or SQLite for local dev
    DATABASE_URL: str = "sqlite:///./datalyze.db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
