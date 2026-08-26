from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.api.v1.router import api_router
from app.middleware.tenant_middleware import TenantScopingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)
    
    # Ensure SQLite columns exist if upgrading existing databases
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in res.fetchall()]
            if "username" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(100)"))
            if "phone_number" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Datalyze: AI-Powered Business Intelligence & Decision Intelligence SaaS Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant Scoping Middleware
app.add_middleware(TenantScopingMiddleware)

# Mount API v1 Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "platform": "Datalyze",
        "tagline": "From Data to Decisions",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }
