import json
import logging
from typing import List, Union, Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator

logger = logging.getLogger("datalyze.security")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Datalyze"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    VERCEL: bool = False
    DATALYZE_SCHEDULER_MODE: Literal["manual", "vercel_daily"] = "manual"
    CRON_SECRET: Optional[str] = Field(default=None, repr=False)
    
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
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=50 * 1024 * 1024, gt=0, validation_alias="MAX_UPLOAD_SIZE_BYTES")
    MAX_REQUEST_SIZE_BYTES: Optional[int] = Field(default=None, gt=0)
    MAX_RESPONSE_SIZE_BYTES: Optional[int] = Field(default=None, gt=0)
    S3_BUCKET_NAME: Optional[str] = Field(default=None, validation_alias="S3_BUCKET_NAME")
    S3_ENDPOINT_URL: Optional[str] = Field(default=None, validation_alias="S3_ENDPOINT_URL")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="auto", validation_alias="AWS_REGION")

    @model_validator(mode="after")
    def apply_host_limits(self):
        if self.VERCEL:
            # Leave room below the platform's 4.5 MB envelope for multipart headers.
            self.MAX_UPLOAD_SIZE_BYTES = min(self.MAX_UPLOAD_SIZE_BYTES, 4_000_000)
            self.MAX_REQUEST_SIZE_BYTES = min(self.MAX_REQUEST_SIZE_BYTES or 4_250_000, 4_250_000)
            self.MAX_RESPONSE_SIZE_BYTES = min(self.MAX_RESPONSE_SIZE_BYTES or 4_000_000, 4_000_000)
            if self.STORAGE_BACKEND == "local":
                raise ValueError("Vercel requires durable dataset storage; use STORAGE_BACKEND=db.")
            if self.STORAGE_BACKEND == "auto":
                self.STORAGE_BACKEND = "db"
        return self

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
        # Defaults belong to the field declaration. An explicit allowlist,
        # including an empty list, must never gain additional trusted sites.
        if isinstance(v, str):
            value = v.strip()
            origins = json.loads(value) if value.startswith("[") else value.split(",")
        else:
            origins = v
        if not isinstance(origins, list) or any(not isinstance(item, str) for item in origins):
            raise ValueError("CORS_ORIGINS must be a list of origin strings.")
        return list(dict.fromkeys(item.strip().rstrip("/") for item in origins if item.strip()))

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("ENVIRONMENT", "development").lower() == "production":
            if "change-in-production" in v or len(v) < 32:
                raise ValueError("CRITICAL SECURITY ERROR: Production SECRET_KEY must be a strong random secret set via environment variable.")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()


