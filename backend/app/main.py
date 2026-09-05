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

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import DatalyzeException

app_logger = logging.getLogger("datalyze.app")

@app.exception_handler(DatalyzeException)
async def datalyze_exception_handler(request: Request, exc: DatalyzeException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "status_code": 422}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled Server Error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal error occurred: {str(exc)}", "status_code": 500}
    )


@app.get("/")
def root():
    return {
        "platform": "Datalyze",
        "tagline": "From Data to Decisions",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }

