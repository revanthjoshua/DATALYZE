import pytest
import io
import time
from app.models.uploaded_dataset import UploadedDataset
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.models.detection_event import DetectionEvent
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.alert import Alert
from app.services.dataset_store import TenantDatasetStore


def test_dataset_upload_persistence_and_multi_tenant_isolation(client, db_session):
    """
    Verifies that:
    1. Uploaded datasets are recorded in the database (UploadedDataset table).
    2. Tenant A and Tenant B have separate, isolated datasets and analytics.
    3. Deleting Tenant A's dataset purges only Tenant A's data and leaves Tenant B intact.
    4. Both backend and frontend endpoints return clean empty states.
    """
    suffix = str(int(time.time()))
    TenantDatasetStore.clear_all()

    # 1. Register Company A
    res_a = client.post("/api/v1/auth/register-admin", json={
        "full_name": f"Admin Company A {suffix}",
        "phone_number": "+1555111222",
        "email": f"admin_a_{suffix}@companya.com",
        "username": f"admin_a_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": f"Company A Workspace {suffix}",
        "industry": "Retail/E-commerce"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    comp_a_id = res_a.json()["company"]["id"]

    # 2. Register Company B
    res_b = client.post("/api/v1/auth/register-admin", json={
        "full_name": f"Admin Company B {suffix}",
        "phone_number": "+1555333444",
        "email": f"admin_b_{suffix}@companyb.com",
        "username": f"admin_b_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": f"Company B Workspace {suffix}",
        "industry": "SaaS/Technology"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    comp_b_id = res_b.json()["company"]["id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Verify both start with has_dataset: False
    info_a_init = client.get("/api/v1/data/dataset/info", headers=headers_a).json()
    assert info_a_init["has_dataset"] is False

    info_b_init = client.get("/api/v1/data/dataset/info", headers=headers_b).json()
    assert info_b_init["has_dataset"] is False

    # 3. Company A uploads CSV
    csv_content_a = (
        "date,revenue,units,region\n"
        "2026-08-01,500.0,5,North\n"
        "2026-08-02,750.0,8,South\n"
        "2026-08-03,620.0,6,East\n"
    )
    upload_res_a = client.post(
        "/api/v1/data/upload",
        headers=headers_a,
        files={"file": ("dataset_a.csv", io.BytesIO(csv_content_a.encode("utf-8")), "text/csv")}
    )
    assert upload_res_a.status_code == 200
    assert upload_res_a.json()["status"] == "success"

    # Verify UploadedDataset record exists in DB for Company A
    dataset_rec_a = db_session.query(UploadedDataset).filter(UploadedDataset.company_id == comp_a_id).first()
    assert dataset_rec_a is not None
    assert dataset_rec_a.filename == "dataset_a.csv"
    assert dataset_rec_a.row_count == 3

    # Verify Company B still sees has_dataset: False and 0 KPIs
    info_b = client.get("/api/v1/data/dataset/info", headers=headers_b).json()
    assert info_b["has_dataset"] is False

    kpis_b = client.get("/api/v1/kpis", headers=headers_b).json()
    assert len(kpis_b) == 0

    # 4. Company B uploads its own CSV
    csv_content_b = (
        "date,mrr,churn_rate\n"
        "2026-08-01,25000.0,1.2\n"
        "2026-08-02,26000.0,1.1\n"
    )
    upload_res_b = client.post(
        "/api/v1/data/upload",
        headers=headers_b,
        files={"file": ("dataset_b.csv", io.BytesIO(csv_content_b.encode("utf-8")), "text/csv")}
    )
    assert upload_res_b.status_code == 200
    assert upload_res_b.json()["status"] == "success"

    # 5. Verify Company A and B see ONLY their own data
    info_a = client.get("/api/v1/data/dataset/info", headers=headers_a).json()
    assert info_a["has_dataset"] is True
    assert info_a["filename"] == "dataset_a.csv"
    assert "revenue" in info_a["numeric_columns"]

    info_b_after = client.get("/api/v1/data/dataset/info", headers=headers_b).json()
    assert info_b_after["has_dataset"] is True
    assert info_b_after["filename"] == "dataset_b.csv"
    assert "mrr" in info_b_after["numeric_columns"]
    assert "revenue" not in info_b_after["numeric_columns"]

    # 6. Company A calls DELETE /api/v1/data/dataset
    del_res_a = client.delete("/api/v1/data/dataset", headers=headers_a)
    assert del_res_a.status_code == 200
    assert del_res_a.json()["success"] is True

    # Verify Company A returns to clean empty state
    info_a_deleted = client.get("/api/v1/data/dataset/info", headers=headers_a).json()
    assert info_a_deleted["has_dataset"] is False

    kpis_a_deleted = client.get("/api/v1/kpis", headers=headers_a).json()
    assert len(kpis_a_deleted) == 0

    assert db_session.query(UploadedDataset).filter(UploadedDataset.company_id == comp_a_id).count() == 0
    assert db_session.query(KPIDefinition).filter(KPIDefinition.company_id == comp_a_id).count() == 0
    assert db_session.query(KPIValue).filter(KPIValue.company_id == comp_a_id).count() == 0

    # 7. Verify Company B is completely unaffected
    info_b_final = client.get("/api/v1/data/dataset/info", headers=headers_b).json()
    assert info_b_final["has_dataset"] is True
    assert info_b_final["filename"] == "dataset_b.csv"

    kpis_b_final = client.get("/api/v1/kpis", headers=headers_b).json()
    assert len(kpis_b_final) > 0
    assert db_session.query(UploadedDataset).filter(UploadedDataset.company_id == comp_b_id).count() == 1
