"""Bound browser transfers without truncating or deleting stored datasets."""
from fastapi import HTTPException
from starlette.responses import JSONResponse

from app.core.config import settings


def check_response_size(content: str | bytes, action: str) -> None:
    limit = settings.MAX_RESPONSE_SIZE_BYTES
    if limit is None:
        return
    size = len(content.encode('utf-8') if isinstance(content, str) else content)
    if size > limit:
        raise HTTPException(413, f'{action} exceeds this host’s {limit / 1_000_000:g} MB transfer limit. '
                            'The stored dataset is unchanged. Use a local deployment connected to this database '
                            'to access the complete data, or prepare a smaller dataset.')


def check_json_response(payload: dict, action: str) -> None:
    if settings.MAX_RESPONSE_SIZE_BYTES is not None:
        check_response_size(JSONResponse(payload).body, action)
