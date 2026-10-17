"""HTTP regression: test isolation must never bypass auth request limits."""
import pytest

from app.middleware.rate_limit_middleware import RATE_LIMIT_RULES


def test_forged_forwarded_ips_cannot_bypass_login_limit(client):
    path = "/api/v1/auth/login"
    _, maximum = RATE_LIMIT_RULES[path]
    # Invalid payloads never authenticate, but they must still consume a slot.
    for index in range(maximum):
        response = client.post(path, json={}, headers={
            "X-Forwarded-For": f"198.51.100.{index + 1}",
        })
        assert response.status_code == 422

    rejected = client.post(path, json={}, headers={"X-Forwarded-For": "203.0.113.99"})
    assert rejected.status_code == 429
    retry_after = int(rejected.headers["Retry-After"])
    assert retry_after > 0
    assert rejected.json()["retry_after_seconds"] == retry_after
    # Limiting authentication does not make the service liveness endpoint fail.
    assert client.get("/").status_code == 200


@pytest.mark.parametrize("origin,allowed", [
    ("http://localhost:5173", True),
    ("https://untrusted.example", False),
])
def test_rate_limit_response_preserves_cors_policy_and_request_id(client, origin, allowed):
    path = "/api/v1/auth/login"
    _, maximum = RATE_LIMIT_RULES[path]
    for _ in range(maximum):
        assert client.post(path, json={}).status_code == 422

    rejected = client.post(path, json={}, headers={"Origin": origin})
    assert rejected.status_code == 429
    assert rejected.headers["X-Request-ID"].strip()
    assert int(rejected.headers["Retry-After"]) > 0
    assert rejected.json()["retry_after_seconds"] == int(rejected.headers["Retry-After"])
    if allowed:
        assert rejected.headers["Access-Control-Allow-Origin"] == origin
        assert rejected.headers["Access-Control-Allow-Credentials"] == "true"
        exposed = {header.strip().lower() for header in rejected.headers["Access-Control-Expose-Headers"].split(",")}
        assert {"x-request-id", "retry-after"} <= exposed
    else:
        assert "Access-Control-Allow-Origin" not in rejected.headers
