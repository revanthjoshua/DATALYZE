import sys
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.company import Company
from app.models.user import User
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def test_rbac_matrix():
    print("Testing End-to-End RBAC Security Matrix across Roles...")
    db = SessionLocal()
    
    # 1. Setup Tenant and Users
    company = db.query(Company).filter(Company.name == "RBAC Test Corp").first()
    if not company:
        company = Company(name="RBAC Test Corp", industry="SaaS & Tech", currency="USD", timezone="UTC")
        db.add(company)
        db.commit()
        db.refresh(company)

    # Admin User
    admin = db.query(User).filter(User.email == "admin@rbac.datalyze.ai").first()
    if not admin:
        admin = User(email="admin@rbac.datalyze.ai", hashed_password=hash_password("Pass123!"), full_name="Admin User", role="company admin", company_id=company.id)
        db.add(admin)
    
    # Analyst User
    analyst = db.query(User).filter(User.email == "analyst@rbac.datalyze.ai").first()
    if not analyst:
        analyst = User(email="analyst@rbac.datalyze.ai", hashed_password=hash_password("Pass123!"), full_name="Analyst User", role="analyst", company_id=company.id)
        db.add(analyst)
    
    # Viewer User
    viewer = db.query(User).filter(User.email == "viewer@rbac.datalyze.ai").first()
    if not viewer:
        viewer = User(email="viewer@rbac.datalyze.ai", hashed_password=hash_password("Pass123!"), full_name="Viewer User", role="viewer", company_id=company.id)
        db.add(viewer)
        
    db.commit()
    db.refresh(admin)
    db.refresh(analyst)
    db.refresh(viewer)

    admin_token = create_access_token({"sub": str(admin.id), "company_id": company.id, "role": admin.role})
    analyst_token = create_access_token({"sub": str(analyst.id), "company_id": company.id, "role": analyst.role})
    viewer_token = create_access_token({"sub": str(viewer.id), "company_id": company.id, "role": viewer.role})

    admin_hdr = {"Authorization": f"Bearer {admin_token}"}
    analyst_hdr = {"Authorization": f"Bearer {analyst_token}"}
    viewer_hdr = {"Authorization": f"Bearer {viewer_token}"}

    # ----------------------------------------------------
    # TEST 1: Admin Permissions (Full Access)
    # ----------------------------------------------------
    # Admin can update company
    res = client.put("/api/v1/company", json={"name": "RBAC Test Corp Updated"}, headers=admin_hdr)
    assert res.status_code == 200, f"Admin update company failed: {res.text}"
    print("[PASS] Admin updated company settings successfully (HTTP 200)")

    # Admin can upload data
    csv_data = "date,mrr,churn_rate\n2026-08-01,15000,0.02\n2026-08-02,15200,0.019\n"
    res = client.post("/api/v1/data/upload", files={"file": ("saas_metrics.csv", csv_data, "text/csv")}, headers=admin_hdr)
    assert res.status_code == 200
    print("[PASS] Admin uploaded dataset successfully (HTTP 200)")

    # ----------------------------------------------------
    # TEST 2: Analyst Permissions (Operational Write, No Admin Settings)
    # ----------------------------------------------------
    # Analyst CAN upload data
    res = client.post("/api/v1/data/upload", files={"file": ("analyst_data.csv", csv_data, "text/csv")}, headers=analyst_hdr)
    assert res.status_code == 200
    print("[PASS] Analyst uploaded dataset successfully (HTTP 200)")

    # Analyst CAN acknowledge anomalies
    res = client.post("/api/v1/detections/acknowledge-all", headers=analyst_hdr)
    assert res.status_code == 200
    print("[PASS] Analyst acknowledged anomalies successfully (HTTP 200)")

    # Analyst CANNOT update company settings (HTTP 403)
    res = client.put("/api/v1/company", json={"name": "Analyst Hack"}, headers=analyst_hdr)
    assert res.status_code == 403, f"Expected 403 Forbidden for analyst modifying company, got {res.status_code}"
    print("[PASS] Analyst blocked from modifying company settings (HTTP 403 Forbidden)")

    # Analyst CANNOT invite new users (HTTP 403)
    res = client.post("/api/v1/company/invite", json={"email": "newuser@rbac.com", "role": "analyst"}, headers=analyst_hdr)
    assert res.status_code == 403, f"Expected 403 Forbidden for analyst inviting users, got {res.status_code}"
    print("[PASS] Analyst blocked from inviting team members (HTTP 403 Forbidden)")

    # ----------------------------------------------------
    # TEST 3: Viewer Permissions (Read-Only, Blocked on ALL Writes)
    # ----------------------------------------------------
    # Viewer CAN read company info
    res = client.get("/api/v1/company", headers=viewer_hdr)
    assert res.status_code == 200
    print("[PASS] Viewer can read company settings (HTTP 200)")

    # Viewer CAN read KPI summary
    res = client.get("/api/v1/kpis/summary", headers=viewer_hdr)
    assert res.status_code == 200
    print("[PASS] Viewer can read KPI summary (HTTP 200)")

    # Viewer CAN read Detections
    res = client.get("/api/v1/detections", headers=viewer_hdr)
    assert res.status_code == 200
    print("[PASS] Viewer can read detections list (HTTP 200)")

    # Viewer CANNOT upload data (HTTP 403)
    res = client.post("/api/v1/data/upload", files={"file": ("viewer_data.csv", csv_data, "text/csv")}, headers=viewer_hdr)
    assert res.status_code == 403, f"Expected 403 for viewer uploading data, got {res.status_code}"
    print("[PASS] Viewer blocked from uploading data (HTTP 403 Forbidden)")

    # Viewer CANNOT acknowledge anomalies (HTTP 403)
    res = client.post("/api/v1/detections/acknowledge-all", headers=viewer_hdr)
    assert res.status_code == 403, f"Expected 403 for viewer acknowledging alerts, got {res.status_code}"
    print("[PASS] Viewer blocked from acknowledging alerts (HTTP 403 Forbidden)")

    # Viewer CANNOT approve inventory transfers (HTTP 403)
    res = client.post("/api/v1/inventory/transfers/1/approve", headers=viewer_hdr)
    assert res.status_code == 403, f"Expected 403 for viewer approving transfers, got {res.status_code}"
    print("[PASS] Viewer blocked from approving inventory transfers (HTTP 403 Forbidden)")

    # Viewer CANNOT update company settings (HTTP 403)
    res = client.put("/api/v1/company", json={"name": "Viewer Hack"}, headers=viewer_hdr)
    assert res.status_code == 403, f"Expected 403 for viewer modifying company, got {res.status_code}"
    print("[PASS] Viewer blocked from modifying company settings (HTTP 403 Forbidden)")

    print("\n=======================================================")
    print("RBAC ACCESS CONTROL MATRIX VERIFIED AND 100% ENFORCED!")
    print("=======================================================")

if __name__ == "__main__":
    test_rbac_matrix()
