"""HTTP regression: test isolation must never bypass auth request limits."""
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
