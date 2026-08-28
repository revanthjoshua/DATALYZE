import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

db_url = settings.DATABASE_URL or "sqlite:///./datalyze.db"

# Engine configuration tailored for Neon PostgreSQL and Serverless / Local SQLite
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
elif os.getenv("VERCEL") or settings.ENVIRONMENT.lower() == "production":
    # Serverless / Neon Postgres pooled configuration
    engine = create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )
else:
    engine = create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()