import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.services.dataset_store import TenantDatasetStore
from app.services.data_processing_service import DataProcessingService
from app.services.noah_service import NoahService
from app.services.root_cause_service import RootCauseService
from app.schemas.noah_schema import NoahQueryRequest
from app.models.detection_event import DetectionEvent
from app.models.kpi_definition import KPIDefinition


def get_admin_auth(client: TestClient, email: str = "stabilization_admin@datalyze.com") -> dict:
    reg = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Stabilization Admin",
        "phone_number": "+15559988",
        "email": email,
        "username": email.split("@")[0],
        "password": "AdminPassword123!",
        "confirm_password": "AdminPassword123!",
        "company_name": "Stabilization Test Workspace",
        "industry": "Technology"
    })
    if reg.status_code == 201:
        token = reg.json()["access_token"]
    else:
        login = client.post("/api/v1/auth/login", json={
            "identifier": email,
            "password": "AdminPassword123!",
            "portal_type": "admin"
        })
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_cors_vercel_origin_regex(client: TestClient):
    """Verifies that Vercel production and preview domains pass CORS preflight OPTIONS."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://datalyze-y9n8.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://datalyze-y9n8.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preview_vercel_domain(client: TestClient):
    """Verifies that arbitrary Vercel preview URLs match allow_origin_regex."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://datalyze-preview-pr-12.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://datalyze-preview-pr-12.vercel.app"


def test_serverless_dataset_auto_hydration_for_noah_and_root_cause(
    client: TestClient,
    db_session: Session
):
    """
    Simulates a serverless cold-start by uploading a dataset,
    clearing the in-memory TenantDatasetStore, and verifying that Noah AI
    and RootCauseService automatically restore from database storage.
    """
    auth_headers = get_admin_auth(client, "coldstart_admin@datalyze.com")

    # 1. Ingest sample dataset
    csv_content = (
        "date,revenue,units_sold,channel,region\n"
        "2026-01-01,15000,120,Online,North America\n"
        "2026-01-02,18500,145,Retail,Europe\n"
        "2026-01-03,12000,95,Online,Asia\n"
        "2026-01-04,22000,180,Direct,North America\n"
    )
    file = io.BytesIO(csv_content.encode("utf-8"))
    upload_res = client.post(
        "/api/v1/data/upload",
        files={"file": ("sales_pipeline.csv", file, "text/csv")},
        headers=auth_headers
    )
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    tenant_id = me_res.json()["user"]["company_id"]

    # 2. Simulate serverless container restart: wipe in-memory store
    TenantDatasetStore.clear_dataset(tenant_id)
    assert TenantDatasetStore.get_metadata(tenant_id) is None

    # 3. Query Noah AI - should auto-hydrate dataset
    noah_res = client.post(
        "/api/v1/noah/query",
        json={"question": "What is the total revenue in our uploaded dataset?"},
        headers=auth_headers
    )
    assert noah_res.status_code == 200
    noah_data = noah_res.json()
    assert "answer" in noah_data
    assert len(noah_data["answer"]) > 0

    # 4. Verify Root Cause Service auto-hydrates
    TenantDatasetStore.clear_dataset(tenant_id)
    assert TenantDatasetStore.get_dataset(tenant_id) is None

    kpi = db_session.query(KPIDefinition).filter(KPIDefinition.company_id == tenant_id).first()
    assert kpi is not None

    detection = DetectionEvent(
        company_id=tenant_id,
        kpi_id=kpi.id,
        direction="down",
        severity="critical",
        status="active",
        magnitude=6500.0,
        current_value=12000.0,
        baseline_value=18500.0,
        percentage_change=-35.1,
    )
    db_session.add(detection)
    db_session.commit()
    db_session.refresh(detection)

    rc_service = RootCauseService(db_session, tenant_id=tenant_id)
    root_causes = rc_service.explain_detection(detection)
    assert len(root_causes) > 0


def test_report_csv_export_endpoints(client: TestClient):
    """Verifies that report CSV endpoints return valid CSV attachments."""
    auth_headers = get_admin_auth(client, "reports_admin@datalyze.com")
    res = client.get("/api/v1/reports/kpi-summary-csv", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=datalyze_kpi_summary.csv" in res.headers["content-disposition"]
    assert len(res.content) > 0
