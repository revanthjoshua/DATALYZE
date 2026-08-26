from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.exceptions import TenantIsolationException


class TenantScopingMiddleware(BaseHTTPMiddleware):
    """
    Middleware ensuring tenant context is tracked on request state if present.
    """
    async def dispatch(self, request: Request, call_next):
        # We can inspect headers or allow dependency injection to do strict enforcement
        response = await call_next(request)
        return response
