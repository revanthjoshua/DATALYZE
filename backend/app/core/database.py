from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

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
elif settings.VERCEL:
    # Neon provides the shared transaction pool. Do not retain up to fifteen
    # additional connections in every short-lived Vercel function instance.
    options = {"connect_timeout": 10} if db_url.startswith(("postgresql+psycopg2:", "postgresql+psycopg:")) else {}
    engine = create_engine(db_url, echo=False, poolclass=NullPool, connect_args=options)
elif settings.ENVIRONMENT.lower() == "production":
    # A continuously running API may keep a bounded local connection pool.
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
