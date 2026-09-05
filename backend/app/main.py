from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.api.v1.router import api_router
from app.middleware.tenant_middleware import TenantScopingMiddleware
from app.middleware.request_id_middleware import RequestIDMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In local SQLite development only, ensure tables exist if not running Alembic migrations
    if settings.DATABASE_URL.startswith("sqlite") and settings.ENVIRONMENT.lower() != "production":
        Base.metadata.create_all(bind=engine)
    
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Datalyze: AI-Powered Business Intelligence & Decision Intelligence SaaS Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

cors_origins = list(settings.CORS_ORIGINS)
frontend_origin = settings.FRONTEND_URL.rstrip("/")
if frontend_origin and frontend_origin not in cors_origins:
    cors_origins.append(frontend_origin)

# 1. Request ID Correlation Middleware (outermost)
app.add_middleware(RequestIDMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# 3. Rate Limit Middleware (protects sensitive auth routes)
app.add_middleware(RateLimitMiddleware)

# 4. Tenant Scoping Middleware
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

