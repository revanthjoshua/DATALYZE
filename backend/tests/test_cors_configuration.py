"""Deployment allowlists must not inherit old or local frontend access."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.core.config import Settings


def test_explicit_cors_allowlist_is_exact():
    configured = Settings(_env_file=None, CORS_ORIGINS=["https://workspace.example"])
    assert configured.CORS_ORIGINS == ["https://workspace.example"]
    assert Settings(_env_file=None, CORS_ORIGINS=[]).CORS_ORIGINS == []


def test_cors_local_defaults_and_json_environment(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings(_env_file=None).CORS_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]
    monkeypatch.setenv("CORS_ORIGINS", '["https://workspace.example"]')
    assert Settings(_env_file=None).CORS_ORIGINS == ["https://workspace.example"]


@pytest.mark.parametrize("origins", ["[malformed]", [123], {"origin": "https://workspace.example"}])
def test_malformed_cors_is_rejected(origins):
    with pytest.raises(ValueError):
        Settings(_env_file=None, CORS_ORIGINS=origins)


def test_production_app_preflight_only_accepts_configured_origin(tmp_path):
    # A separate import tests the actual production middleware configuration,
    # without mutating the application's shared test instance or reading .env.
    env = dict(os.environ, ENVIRONMENT="production", DATABASE_URL="sqlite:///:memory:",
               SECRET_KEY="cors-test-only-strong-key-not-used-in-production-2026",
               CORS_ORIGINS='["https://workspace.example"]',
               FRONTEND_URL="https://email-links.example", RESEND_API_KEY="",
               DATALYZE_MONITOR_INTERVAL_SECONDS="0", PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    script = """
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
origins = ['https://workspace.example', 'https://email-links.example',
           'https://datalyze-y9n8.vercel.app', 'http://localhost:5173', 'http://127.0.0.1:5173']
result = {}
for origin in origins:
    response = client.options('/api/v1/auth/login', headers={
        'Origin': origin, 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'})
    result[origin] = [response.status_code, response.headers.get('access-control-allow-origin')]
print(json.dumps(result))
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=45, check=True)
    responses = json.loads(result.stdout.strip())
    assert responses.pop("https://workspace.example") == [200, "https://workspace.example"]
    assert all(response == [400, None] for response in responses.values())
