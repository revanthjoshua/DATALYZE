import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_live_server():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    suffix = str(int(time.time()))
    print("\n" + "=" * 70)
    print("  DATALYZE LIVE SERVER END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Employee registration on nonexistent workspace
    print("\n[1] Testing Employee Registration on Nonexistent Workspace...")
    res = client.post("/auth/register-employee", json={
        "full_name": "Orphan Staff",
        "phone_number": "+1555000111",
        "email": f"orphan_{suffix}@randominvalidcorp.com",
        "username": f"orphan_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": "Nonexistent Workspace XYZ"
    })
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    assert "No workspace found" in res.json()["detail"]
    print("  -> PASS: Correctly rejected with 400 Bad Request.")

    # 2. Admin Registration
    print("\n[2] Testing Admin Registration (Creating Workspace)...")
    comp_name = f"Vance Dynamics {suffix}"
    admin_email = f"elena_{suffix}@vancedynamics.com"
    admin_user = f"elena_{suffix}"
    admin_reg = client.post("/auth/register-admin", json={
        "full_name": "Dr. Elena Vance",
        "phone_number": f"+1555{suffix[-4:]}1",
        "email": admin_email,
        "username": admin_user,
        "password": "VancePassword123!",
        "confirm_password": "VancePassword123!",
        "company_name": comp_name,
        "industry": "Retail/E-commerce"
    })
    assert admin_reg.status_code == 201, f"Admin reg failed: {admin_reg.text}"
    admin_token = admin_reg.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert "X-Request-ID" in admin_reg.headers
    print("  -> PASS: Company Workspace & Admin created. Correlation ID attached.")

    # 3. Employee Registration joining Vance Dynamics
    print("\n[3] Testing Employee Registration (Joining Vance Dynamics)...")
    emp_email = f"gordon_{suffix}@vancedynamics.com"
    emp_user = f"gordon_{suffix}"
    emp_reg = client.post("/auth/register-employee", json={
        "full_name": "Gordon Freeman",
        "phone_number": f"+1555{suffix[-4:]}2",
        "email": emp_email,
        "username": emp_user,
        "company_name": comp_name,
        "password": "GordonPassword123!",
        "confirm_password": "GordonPassword123!"
    })
    assert emp_reg.status_code == 201, f"Emp reg failed: {emp_reg.text}"
    emp_token = emp_reg.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}
    print("  -> PASS: Employee joined existing company workspace successfully.")

    # 4. Portal Role Segregation
    print("\n[4] Testing Portal Role Segregation (403 Enforcement)...")
    emp_admin_portal = client.post("/auth/login", json={
        "identifier": emp_user,
        "password": "GordonPassword123!",
        "portal_type": "admin"
    })
    assert emp_admin_portal.status_code == 403
    print("  -> PASS: Employee accessing Admin Portal rejected with 403 Forbidden.")

    admin_emp_portal = client.post("/auth/login", json={
        "identifier": admin_user,
        "password": "VancePassword123!",
        "portal_type": "employee"
    })
    assert admin_emp_portal.status_code == 403
    print("  -> PASS: Admin accessing Employee Portal rejected with 403 Forbidden.")

    # 5. Legitimate Login
    print("\n[5] Testing Legitimate Authentication...")
    admin_login = client.post("/auth/login", json={
        "identifier": admin_user,
        "password": "VancePassword123!",
        "portal_type": "admin"
    })
    assert admin_login.status_code == 200
    print("  -> PASS: Admin authenticated successfully.")

    emp_login = client.post("/auth/login", json={
        "identifier": emp_user,
        "password": "GordonPassword123!",
        "portal_type": "employee"
    })
    assert emp_login.status_code == 200
    print("  -> PASS: Employee authenticated successfully.")

    # 6. Load Sample Dataset
    print("\n[6] Testing Data Ingestion Pipeline...")
    load_res = client.post("/data/load-sample", headers=admin_headers)
    assert load_res.status_code == 200
    print("  -> PASS: 30-Day Sample Ingestion succeeded.")

    # 7. KPI Metrics & Detections
    print("\n[7] Testing KPI Intelligence & Anomaly Engine...")
    kpis = client.get("/kpis", headers=admin_headers).json()
    assert len(kpis) > 0
    print(f"  -> PASS: {len(kpis)} KPIs loaded.")

    det_res = client.post("/detections/run", headers=admin_headers)
    assert det_res.status_code == 200
    detections = det_res.json()
    print(f"  -> PASS: Anomaly Detection executed ({len(detections)} anomalies found).")

    if detections:
        det_id = detections[0]["id"]
        # Root cause analysis
        rc_res = client.get(f"/detections/{det_id}/root-causes", headers=admin_headers)
        assert rc_res.status_code == 200
        print(f"  -> PASS: Root-Cause analysis retrieved for anomaly {det_id}.")

        # Acknowledge anomaly
        ack_res = client.post(f"/detections/{det_id}/acknowledge", headers=admin_headers)
        assert ack_res.status_code == 200
        print(f"  -> PASS: Anomaly {det_id} acknowledged successfully.")

    # 8. Predictions & Recommendations
    print("\n[8] Testing Forecasting & Prescriptive Recommendation Engines...")
    pred_res = client.post("/predictions/generate?horizon_days=7", headers=admin_headers)
    assert pred_res.status_code == 200
    print(f"  -> PASS: 7-Day Forecast generated ({len(pred_res.json())} prediction points).")

    rec_res = client.post("/recommendations/generate", headers=admin_headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    print(f"  -> PASS: Recommendations generated ({len(recs)} action items).")

    if recs:
        rec_id = recs[0]["id"]
        status_res = client.post(f"/recommendations/{rec_id}/status?status=completed", headers=admin_headers)
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "completed"
        print(f"  -> PASS: Recommendation {rec_id} status updated to 'completed'.")

    # 9. Smart Inventory Intelligence
    print("\n[9] Testing Smart Inventory Intelligence & Transfer Approval...")
    inv_res = client.post("/inventory/reseed-sample", headers=admin_headers)
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert len(inv_data["items"]) > 0
    first_item = inv_data["items"][0]
    transfer_res = client.post(f"/inventory/transfers/{first_item['id']}/approve?quantity=25", headers=admin_headers)
    assert transfer_res.status_code == 200
    print(f"  -> PASS: Inventory transfer approved for item {first_item['name']}.")

    # 10. Noah AI Assistant
    print("\n[10] Testing Noah AI Conversational & Agentic Gating...")
    noah_res = client.post("/noah/query", headers=admin_headers, json={
        "question": "What is our current revenue outlook and stock risk?"
    })
    assert noah_res.status_code == 200
    assert len(noah_res.json()["answer"]) > 10
    print("  -> PASS: Noah conversational response generated.")

    noah_agentic = client.post("/noah/agentic-reasoning", headers=admin_headers, json={
        "goal": "Autonomous execution"
    })
    assert noah_agentic.status_code == 403
    print("  -> PASS: Agentic reasoning securely 403-gated for Phase 5.")

    # 11. Password Reset Flow
    print("\n[11] Testing 3-Step Password Reset Flow...")
    otp_req = client.post("/auth/forgot-password/request", json={
        "identifier": admin_email,
        "portal_type": "admin"
    })
    assert otp_req.status_code == 200
    assert "code_preview" not in otp_req.json()
    from app.services.email_service import email_service
    otp_code = email_service.sent_otps.get(admin_email, email_service.last_sent_otp)
    assert otp_code is not None and len(otp_code) == 6

    otp_ver = client.post("/auth/forgot-password/verify", json={
        "identifier": admin_email,
        "code": otp_code,
        "portal_type": "admin"
    })
    assert otp_ver.status_code == 200

    otp_conf = client.post("/auth/forgot-password/confirm", json={
        "identifier": admin_email,
        "code": otp_code,
        "new_password": "NewVancePassword2026!",
        "confirm_password": "NewVancePassword2026!",
        "portal_type": "admin"
    })
    assert otp_conf.status_code == 200

    old_login = client.post("/auth/login", json={
        "identifier": admin_email,
        "password": "VancePassword123!",
        "portal_type": "admin"
    })
    assert old_login.status_code == 401
    print("  -> PASS: Old password rejected with 401.")

    new_login = client.post("/auth/login", json={
        "identifier": admin_email,
        "password": "NewVancePassword2026!",
        "portal_type": "admin"
    })
    assert new_login.status_code == 200
    print("  -> PASS: Sign in with new password succeeded.")

    print("\n" + "=" * 70)
    print("  ALL LIVE SERVER TEST SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_live_server()
