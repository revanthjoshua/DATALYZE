import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging import set_request_id, request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a unique correlation ID (X-Request-ID).
    Sets the ID in contextvars for downstream logging and returns it in response headers.
    """
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID")
        if not req_id or not req_id.strip():
            req_id = str(uuid.uuid4())
        
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id
        
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)
