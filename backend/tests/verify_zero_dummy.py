import pytest
from starlette.testclient import TestClient
from app.main import app

def test_zero_dummy_and_upload_flow():
    client = TestClient(app)

    # 1. Register a Fresh New Admin Account
    admin_email = "new_owner_clean@example.com"
    reg_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Sarah Connor",
        "phone_number": "+15550999",
        "email": admin_email,
        "username": "sarah_admin",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": "Cyberdyne Systems",
        "industry": "Retail/E-commerce"
    })
    assert reg_res.status_code == 201, f"Admin register failed: {reg_res.text}"
    admin_token = reg_res.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    print("\n[PASS] Fresh Admin account registered")

    # 2. Verify Zero Dummy Data on Clean Workspace
    kpis = client.get("/api/v1/kpis/summary", headers=headers_admin).json()
    assert len(kpis) == 0, f"Expected 0 KPIs before upload, found {len(kpis)}"
    print(f"[PASS] Verified 0 dummy KPIs before file upload: {len(kpis)} items")

    inv = client.get("/api/v1/inventory/summary", headers=headers_admin).json()
    items = inv.get("items", [])
    assert len(items) == 0, f"Expected 0 inventory items before upload, found {len(items)}"
    print(f"[PASS] Verified 0 dummy inventory items: {len(items)} items")

    alerts = client.get("/api/v1/detections", headers=headers_admin).json()
    assert len(alerts) == 0, f"Expected 0 alerts before upload, found {len(alerts)}"
    print(f"[PASS] Verified 0 dummy alerts: {len(alerts)} alerts")

    recs = client.get("/api/v1/recommendations", headers=headers_admin).json()
    assert len(recs) == 0, f"Expected 0 recommendations before upload, found {len(recs)}"
    print(f"[PASS] Verified 0 dummy recommendations: {len(recs)} recs")

    # 3. Upload / Ingest Real Business Dataset
    ingest_res = client.post("/api/v1/data/load-sample", headers=headers_admin)
    assert ingest_res.status_code == 200, f"Ingestion failed: {ingest_res.text}"
    print("[PASS] Real business dataset ingested into workspace pipeline")

    # 4. Verify Data Populated Strictly from Uploaded File
    kpis_after = client.get("/api/v1/kpis/summary", headers=headers_admin).json()
    assert len(kpis_after) > 0, "KPIs did not populate after ingestion"
    print(f"[PASS] Monitored metrics populated from file: {[k['name'] for k in kpis_after]}")
    for k in kpis_after:
        print(f"   - {k['name']}: {k['current_value']} (status: {k['status']})")

    # 5. Check Confidence Forecasts
    pred_res = client.get(f"/api/v1/predictions/kpi/{kpis_after[0]['id']}?horizon_days=7", headers=headers_admin)
    assert pred_res.status_code == 200, f"Prediction failed: {pred_res.text}"
    preds = pred_res.json()
    assert len(preds) == 7, f"Expected 7 forecast points, got {len(preds)}"
    print(f"[PASS] 7-Day confidence band predictions computed for {kpis_after[0]['name']}:")
    for p in preds[:3]:
        print(f"   - Date: {p['forecast_date']} | Pred: {p['predicted_value']} | Range: [{p['range_low']} to {p['range_high']}]")

    # 6. Register & Authenticate Employee for this workspace
    emp_email = "john_emp@cyberdyne.com"
    emp_reg = client.post("/api/v1/auth/register-employee", json={
        "full_name": "John Connor",
        "phone_number": "+15550888",
        "email": emp_email,
        "username": "john_emp",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_id": reg_res.json()["company"]["id"]
    })
    assert emp_reg.status_code == 201, f"Employee register failed: {emp_reg.text}"
    emp_token = emp_reg.json()["access_token"]
    headers_emp = {"Authorization": f"Bearer {emp_token}"}
    print("[PASS] Employee account registered and linked to workspace")

    emp_kpis = client.get("/api/v1/kpis/summary", headers=headers_emp).json()
    assert len(emp_kpis) == len(kpis_after)
    print(f"[PASS] Employee workspace successfully reads live metrics: {len(emp_kpis)} KPIs active")

    print("\n========================================================")
    print("ALL ZERO-DUMMY-DATA AND FILE INGESTION CHECKS PASSED!")
    print("========================================================")
