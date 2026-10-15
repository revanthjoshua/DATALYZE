from contextlib import asynccontextmanager
import asyncio
import os
from contextlib import suppress
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
    
    interval=int(os.environ.get('DATALYZE_MONITOR_INTERVAL_SECONDS','0'))
    if interval and not 60 <= interval <= 86400:
        raise ValueError('DATALYZE_MONITOR_INTERVAL_SECONDS must be 0 or between 60 and 86400')
    worker=None
    if interval:
        from app.services.monitor_runner import run_cycle
        async def checks():
            while True:
                try:
                    await asyncio.to_thread(run_cycle)
                except Exception:
                    # A transient database/provider failure must not kill monitoring.
                    app_logger.warning('Background cycle failed; the next scheduled cycle will retry.')
                await asyncio.sleep(interval)
        worker=asyncio.create_task(checks())
    try:
        yield
    finally:
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Datalyze: Data Analyst Workspace",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Only explicitly trusted origins receive credentialed cross-origin access.
# FRONTEND_URL controls email links; it does not silently widen this allowlist.
cors_origins = list(settings.CORS_ORIGINS)

# 1. Request ID Correlation Middleware (outermost)
app.add_middleware(RequestIDMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
        content={"detail": "An internal error occurred. Please retry or contact your administrator.", "status_code": 500}
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


@app.get('/health/ready')
def readiness():
    """Read-only probe: a responding process does not establish database readiness."""
    from sqlalchemy import inspect, text
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
            schema = inspect(connection)
            required = ['companies','users','uploaded_datasets','analysis_records','source_refresh_jobs','notification_outbox']
            if any(not schema.has_table(name) for name in required):
                return JSONResponse(status_code=503,content={'status':'not_ready','reason':'Database migrations are required.'})
        return {'status':'ready','database':'available','schema':'available'}
    except Exception:
        return JSONResponse(status_code=503,content={'status':'not_ready','reason':'Database is unavailable.'})

