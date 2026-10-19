import os
# Set isolation before importing the application/configuration, even when tests
# are invoked from the backend directory beside a real .env file.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["STORAGE_BACKEND"] = "db"
os.environ["ENVIRONMENT"] = "test"
os.environ["RESEND_API_KEY"] = ""
# Test origins are explicit and independent of a developer or deployment .env.
os.environ["CORS_ORIGINS"] = '["http://localhost:5173", "http://127.0.0.1:5173"]'
# Operator sources and notification destinations must never run in unit tests.
os.environ["DATALYZE_SOURCES_JSON"] = "[]"
os.environ["DATALYZE_NOTIFICATIONS_JSON"] = "[]"
os.environ["DATALYZE_MONITOR_INTERVAL_SECONDS"] = "0"
os.environ["DATALYZE_SCHEDULER_MODE"] = "manual"
os.environ["CRON_SECRET"] = ""
os.environ["VERCEL"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app

# Use in-memory SQLite for high-speed deterministic test execution
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def isolate_auth_rate_limit(monkeypatch):
    """Tests share an app, but each test starts with its own request window."""
    from app.middleware.rate_limit_middleware import rate_limiter

    # Keep protection active during every test; reset only at test boundaries.
    monkeypatch.delenv("DISABLE_RATE_LIMIT", raising=False)
    rate_limiter.reset()
    try:
        yield
    finally:
        rate_limiter.reset()


@pytest.fixture(autouse=True)
def clean_db_per_test(db_session):
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def accepted_test_email(monkeypatch):
    """No test sends real mail; tests may explicitly override acceptance/failure."""
    from app.services.email_service import email_service
    import resend
    monkeypatch.setattr(email_service, "api_key", "test-only-not-a-real-key")
    monkeypatch.setattr(email_service, "sent_otps", {}, raising=False)
    monkeypatch.setattr(email_service, "last_sent_otp", None, raising=False)
    monkeypatch.setattr(resend.Emails, "send", lambda params: {"id": "test-provider-acceptance"})
    send_otp = email_service.send_password_reset_otp_email

    def record_test_otp(**kwargs):
        email_service.sent_otps[kwargs["to_email"]] = kwargs["otp_code"]
        email_service.last_sent_otp = kwargs["otp_code"]
        return send_otp(**kwargs)

    monkeypatch.setattr(email_service, "send_password_reset_otp_email", record_test_otp)
