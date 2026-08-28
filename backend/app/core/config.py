import json
import logging
from typing import List, Union, Optional
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

    # Database settings: Supports PostgreSQL / SQLite
    DATABASE_URL: str = Field(
        default="sqlite:///./datalyze.db",
        validation_alias="DATABASE_URL"
    )

    # CORS: Restricted strictly to trusted application origins
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        validation_alias="CORS_ORIGINS"
    )

    # Email Service (Resend) Settings
    RESEND_API_KEY: Optional[str] = Field(default=None, validation_alias="RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = Field(default="Datalyze <onboarding@resend.dev>", validation_alias="RESEND_FROM_EMAIL")
    FRONTEND_URL: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_URL")

    # Storage Settings
    STORAGE_BACKEND: str = Field(default="auto", validation_alias="STORAGE_BACKEND")  # auto, local, db, s3
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=50 * 1024 * 1024, validation_alias="MAX_UPLOAD_SIZE_BYTES")  # 50MB
    S3_BUCKET_NAME: Optional[str] = Field(default=None, validation_alias="S3_BUCKET_NAME")
    S3_ENDPOINT_URL: Optional[str] = Field(default=None, validation_alias="S3_ENDPOINT_URL")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="auto", validation_alias="AWS_REGION")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Optional[str]) -> str:
        if not v or not str(v).strip():
            return "sqlite:///./datalyze.db"
        url = str(v).strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        origins = []
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    origins = json.loads(v_str)
                except Exception:
                    origins = [item.strip() for item in v_str.strip("[]").split(",") if item.strip()]
            else:
                origins = [item.strip() for item in v_str.split(",") if item.strip()]
        elif isinstance(v, list):
            origins = [str(item).strip() for item in v if str(item).strip()]
        
        default_dev = ["http://localhost:5173", "http://127.0.0.1:5173"]
        for dev_url in default_dev:
            if dev_url not in origins:
                origins.append(dev_url)
        return origins

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("ENVIRONMENT", "development").lower() == "production":
            if "change-in-production" in v or len(v) < 32:
                raise ValueError("CRITICAL SECURITY ERROR: Production SECRET_KEY must be a strong random secret set via environment variable.")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()


