"""Host quotas reject whole operations; they must never silently truncate data."""
import asyncio
import json

from app.core.config import Settings
from app.middleware.payload_limit_middleware import PayloadLimitMiddleware


def exercise(app, bodies, headers=()):
    messages = [{"type": "http.request", "body": body, "more_body": i < len(bodies) - 1}
                for i, body in enumerate(bodies)]
    output = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        output.append(message)

    asyncio.run(app({"type": "http", "method": "POST", "path": "/", "headers": list(headers)}, receive, send))
    return output


def test_vercel_limits_cannot_be_overridden_above_platform_budget():
    config = Settings(_env_file=None, VERCEL=True, MAX_UPLOAD_SIZE_BYTES=50_000_000,
                      MAX_REQUEST_SIZE_BYTES=50_000_000, MAX_RESPONSE_SIZE_BYTES=50_000_000)
    assert config.MAX_UPLOAD_SIZE_BYTES == 4_000_000
    assert config.MAX_REQUEST_SIZE_BYTES == 4_250_000
    assert config.MAX_RESPONSE_SIZE_BYTES == 4_000_000
    assert config.STORAGE_BACKEND == "db"
    assert Settings(_env_file=None, VERCEL=True, MAX_UPLOAD_SIZE_BYTES=1000).MAX_UPLOAD_SIZE_BYTES == 1000


def test_non_vercel_retains_local_limits():
    config = Settings(_env_file=None, VERCEL=False, MAX_REQUEST_SIZE_BYTES=None, MAX_RESPONSE_SIZE_BYTES=None)
    assert config.MAX_UPLOAD_SIZE_BYTES == 50 * 1024 * 1024
    assert config.MAX_REQUEST_SIZE_BYTES is config.MAX_RESPONSE_SIZE_BYTES is None


def test_oversize_body_never_reaches_mutating_handler():
    called = []

    async def handler(scope, receive, send):
        called.append(True)

    app = PayloadLimitMiddleware(handler, max_request_bytes=8)
    for headers in [(), ((b"content-length", b"2"),), ((b"content-length", b"100"),)]:
        output = exercise(app, [b"12345", b"67890"], headers)
        assert output[0]["status"] == 413
        assert "No changes were made" in json.loads(output[1]["body"])["detail"]
    assert not called


def test_valid_chunked_request_and_response_are_preserved():
    async def handler(scope, receive, send):
        message = await receive()
        assert message == {"type": "http.request", "body": b"12345678", "more_body": False}
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"hello ", "more_body": True})
        await send({"type": "http.response.body", "body": b"world", "more_body": False})

    output = exercise(PayloadLimitMiddleware(handler, 8, 11), [b"1234", b"5678"])
    assert output[0]["status"] == 200
    assert output[1]["body"] == b"hello world"


def test_oversize_response_is_replaced_before_headers_or_partial_data_escape():
    async def handler(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-length", b"600")]})
        await send({"type": "http.response.body", "body": b"x" * 300, "more_body": True})
        await send({"type": "http.response.body", "body": b"y" * 300, "more_body": False})

    output = exercise(PayloadLimitMiddleware(handler, max_response_bytes=500), [b""])
    assert [message["type"] for message in output] == ["http.response.start", "http.response.body"]
    assert output[0]["status"] == 413
    assert "not been truncated" in json.loads(output[1]["body"])["detail"]


def test_vercel_does_not_keep_per_instance_database_pool():
    # Inspect real engine creation in an isolated import without opening a DB.
    import os
    from pathlib import Path
    import subprocess
    import sys
    env = dict(os.environ, VERCEL="1", DATABASE_URL="postgresql://ci:ci@127.0.0.1/unused",
               PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result = subprocess.run([sys.executable, "-c", "from app.core.database import engine; from sqlalchemy.pool import NullPool; assert isinstance(engine.pool, NullPool)"],
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_payload_guard_preserves_cors_request_ids_and_streaming_middleware():
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient
    from app.middleware.request_id_middleware import RequestIDMiddleware
    from app.middleware.tenant_middleware import TenantScopingMiddleware
    from starlette.responses import StreamingResponse

    application = FastAPI()
    saved = []

    @application.post('/echo')
    async def echo(request: Request):
        body = await request.body()
        saved.append(body)
        return {'saved': len(body)}

    @application.get('/large')
    async def large():
        return StreamingResponse(iter([b'x' * 400, b'y' * 400]))

    application.add_middleware(TenantScopingMiddleware)
    application.add_middleware(PayloadLimitMiddleware, max_request_bytes=8, max_response_bytes=500)
    application.add_middleware(CORSMiddleware, allow_origins=['https://preview.example'])
    application.add_middleware(RequestIDMiddleware)
    with TestClient(application) as client:
        valid = client.post('/echo', content=b'12345678')
        assert valid.json() == {'saved': 8}
        for response in [client.post('/echo', content=b'123456789', headers={'Origin':'https://preview.example'}),
                         client.get('/large', headers={'Origin':'https://preview.example'})]:
            assert response.status_code == 413
            assert response.headers['access-control-allow-origin'] == 'https://preview.example'
            assert response.headers['x-request-id']
            assert response.json()['detail']
        assert saved == [b'12345678']
