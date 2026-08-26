import sys
import random
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.company import Company
from app.models.user import User
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def test_data_lifecycle():
    print("Testing Full Data Lifecycle: Empty State vs Populated State across all modules...")
    db = SessionLocal()

    # 1. Create a brand new tenant with ZERO data
    rand_id = random.randint(1000, 999999)
    clean_company = Company(name=f"Clean Lifecycle Corp {rand_id}", industry="Retail & E-Commerce", currency="USD", timezone="UTC")
    db.add(clean_company)
    db.commit()
    db.refresh(clean_company)

    user = User(email=f"lifecycle_{rand_id}@datalyze.ai", hashed_password=hash_password("Pass123!"), full_name="Lifecycle Auditor", role="company admin", company_id=clean_company.id)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "company_id": clean_company.id, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    # ====================================================
    # PHASE A: EMPTY STATE AUDIT
    # ====================================================
    print("\n--- Phase A: Auditing Empty States ---")

    # 1. Dataset Info (Empty)
    res = client.get("/api/v1/data/dataset-info", headers=headers)
    assert res.status_code == 200
    info = res.json()
    assert info.get("has_dataset") is False, "Expected has_dataset=False on empty workspace"
    print("[PASS] Empty State: Dataset Info reports has_dataset=False")

    # 2. KPI Summary (Empty)
    res = client.get("/api/v1/kpis/summary", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 0, "Expected empty KPI list"
    print("[PASS] Empty State: KPI Summary returns clean empty array []")

    # 3. Anomaly Detections (Empty)
    res = client.get("/api/v1/detections", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 0, "Expected empty detections list"
    print("[PASS] Empty State: Anomaly Alerts returns clean empty array []")

    # 4. Recommendations (Empty)
    res = client.get("/api/v1/recommendations", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 0, "Expected empty recommendations list"
    print("[PASS] Empty State: Recommendations returns clean empty array []")

    # 5. Smart Inventory (Empty)
    res = client.get("/api/v1/inventory/summary", headers=headers)
    assert res.status_code == 200
    inv = res.json()
    assert inv["total_items"] == 0 or len(inv["items"]) == 0
    print("[PASS] Empty State: Smart Inventory returns clean zero state")

    # ====================================================
    # PHASE B: POPULATED STATE AUDIT
    # ====================================================
    print("\n--- Phase B: Ingesting Data and Auditing Populated States ---")

    # 1. Ingest 30-Day Multi-Channel Dataset
    res = client.post("/api/v1/data/load-sample", headers=headers)
    assert res.status_code == 200, f"load-sample failed: {res.text}"
    ingest_result = res.json()
    print(f"[PASS] Ingested populated dataset: {ingest_result.get('processed_rows')} rows, {len(ingest_result.get('detected_kpis', []))} detected KPIs")

    # 2. Dataset Info (Populated)
    res = client.get("/api/v1/data/dataset-info", headers=headers)
    assert res.status_code == 200
    info = res.json()
    assert info.get("has_dataset") is True
    assert info.get("row_count") > 0
    print(f"[PASS] Populated State: Dataset Info active with {info['row_count']} rows and {len(info['columns'])} columns")

    # 3. KPI Summary (Populated)
    res = client.get("/api/v1/kpis/summary", headers=headers)
    assert res.status_code == 200
    kpis = res.json()
    assert len(kpis) > 0
    print(f"[PASS] Populated State: {len(kpis)} active KPIs computed (First: {kpis[0]['name']} = {kpis[0]['current_value']})")

    # 4. Predictions (Populated)
    first_kpi_id = kpis[0]["id"]
    res = client.get(f"/api/v1/predictions/kpi/{first_kpi_id}", headers=headers)
    assert res.status_code == 200
    preds = res.json()
    assert len(preds) > 0
    print(f"[PASS] Populated State: {len(preds)} daily forecast projections generated for KPI #{first_kpi_id}")

    # 5. Smart Inventory (Populated via Reseed)
    res = client.post("/api/v1/inventory/reseed-sample", headers=headers)
    assert res.status_code == 200
    inv = res.json()
    assert inv["total_items"] > 0
    assert len(inv["allocations"]) > 0
    print(f"[PASS] Populated State: Inventory has {inv['total_items']} items and {len(inv['allocations'])} transfer recommendations")

    # 6. Execute Transfer Action
    transfer_item = inv["allocations"][0]
    res = client.post(f"/api/v1/inventory/transfers/{transfer_item['item_id']}/approve?quantity=50", headers=headers)
    assert res.status_code == 200
    print(f"[PASS] Action Execution: Transfer approval executed successfully: {res.json().get('message')}")

    # 7. Anomaly Trigger and Acknowledge Lifecycle
    test_ano = client.post("/api/v1/detections/test-anomaly", headers=headers)
    assert test_ano.status_code == 200
    ano_id = test_ano.json()["id"]
    print(f"[PASS] Action Execution: Generated test anomaly #{ano_id}")

    ack_res = client.post(f"/api/v1/detections/{ano_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"
    print(f"[PASS] Action Execution: Acknowledged anomaly #{ano_id}")

    print("\n=======================================================")
    print("DATA LIFECYCLE AUDIT: EMPTY & POPULATED STATES VERIFIED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_data_lifecycle()
