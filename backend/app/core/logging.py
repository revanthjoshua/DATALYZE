import json
import logging
import uuid
import contextvars
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Context variable to track Request/Correlation ID per async task/thread
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id_ctx", default="")

# Standard logger
logger = logging.getLogger("datalyze.audit")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_request_id() -> str:
    req_id = request_id_ctx.get()
    if not req_id:
        req_id = str(uuid.uuid4())
        request_id_ctx.set(req_id)
    return req_id


def set_request_id(req_id: str) -> None:
    request_id_ctx.set(req_id)


# Keys that must never appear in log payloads
REDACTED_KEYS = {
    "password",
    "confirm_password",
    "new_password",
    "old_password",
    "hashed_password",
    "access_token",
    "token",
    "secret",
    "secret_key",
    "otp",
    "code",
    "verification_code",
    "raw_data",
    "file_bytes",
    "content",
}


def sanitize_log_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys from audit log dictionaries."""
    sanitized = {}
    for k, v in d.items():
        k_lower = str(k).lower()
        if any(bad in k_lower for bad in REDACTED_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_log_dict(v)
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [
                sanitize_log_dict(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized


def log_audit_event(
    event: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
    status: str = "SUCCESS"
) -> None:
    """
    Logs a structured security/audit event.
    Guarantees no sensitive data (passwords, tokens, OTPs, raw files) is leaked.
    """
    req_id = get_request_id()
    clean_details = sanitize_log_dict(details or {})
    
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": req_id,
        "event": event,
        "status": status,
        "details": clean_details,
    }

    msg = json.dumps(payload, default=str)
    
    lvl = level.upper()
    if lvl == "WARNING":
        logger.warning(msg)
    elif lvl == "ERROR":
        logger.error(msg)
    elif lvl == "CRITICAL":
        logger.critical(msg)
    else:
        logger.info(msg)
