import time
import os
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.logging import log_audit_event


# Path prefixes/rules for rate limiting: (window_seconds, max_requests)
RATE_LIMIT_RULES: Dict[str, Tuple[int, int]] = {
    "/api/v1/auth/login": (60, 40),
    "/api/v1/auth/register-admin": (60, 30),
    "/api/v1/auth/register-employee": (60, 30),
    "/api/v1/auth/register": (60, 30),
    "/api/v1/auth/forgot-password/request": (60, 20),
    "/api/v1/auth/forgot-password/verify": (60, 30),
    "/api/v1/auth/forgot-password/confirm": (60, 30),
    "/api/v1/auth/invite/verify": (60, 60),
    "/api/v1/auth/invite/accept": (60, 20),
    "/api/v1/company/invite": (60, 30),
}



class RateLimitTracker:
    def __init__(self):
        # key: (client_ip, path) -> list of timestamps
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str, path: str) -> Tuple[bool, int]:
        """
        Returns (is_limited, retry_after_seconds).
        """
        rule = None
        for endpoint_prefix, (window, max_reqs) in RATE_LIMIT_RULES.items():
            if path == endpoint_prefix or path.startswith(endpoint_prefix + "/"):
                rule = (window, max_reqs)
                break

        if not rule:
            return False, 0

        window_sec, max_req = rule
        now = time.time()
        key = f"{client_ip}:{path}"

        # Clean older requests outside the window
        timestamps = [t for t in self.requests[key] if now - t < window_sec]
        self.requests[key] = timestamps

        if len(timestamps) >= max_req:
            oldest = timestamps[0]
            retry_after = int(window_sec - (now - oldest)) + 1
            return True, max(1, retry_after)

        self.requests[key].append(now)
        return False, 0

    def reset(self):
        self.requests.clear()


rate_limiter = RateLimitTracker()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware for sensitive authentication routes.
    Protects against brute-force and credential stuffing attacks.
    """
    async def dispatch(self, request: Request, call_next):
        # Allow disabling in test environments if needed
        if os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true":
            return await call_next(request)

        # Get client IP
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        path = request.url.path

        is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, path)
        if is_limited:
            log_audit_event(
                event="auth_rate_limit_exceeded",
                details={
                    "client_ip": client_ip,
                    "path": path,
                    "retry_after_seconds": retry_after,
                },
                level="WARNING",
                status="RATE_LIMITED"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please wait a moment before trying again.",
                    "retry_after_seconds": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)
