import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_full_state_persistence():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    suffix = str(int(time.time()))
    print("\n" + "=" * 70)
    print("  TESTING PERSISTENCE & DATABASE ROUND-TRIP MUTATIONS")
    print("=" * 70)

    # 1. Register new Admin & Workspace
    comp_name = f"Quantum Retail {suffix}"
    admin_email = f"marcus_{suffix}@quantumretail.com"
    admin_user = f"marcus_{suffix}"
    reg_res = client.post("/auth/register-admin", json={
        "full_name": "Marcus Wright",
        "phone_number": f"+1555{suffix[-4:]}1",
        "email": admin_email,
        "username": admin_user,
        "password": "MarcusPassword123!",
        "confirm_password": "MarcusPassword123!",
        "company_name": comp_name,
        "industry": "Retail/E-commerce"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest Sample Dataset
    print("\n[1] Ingesting Sample Dataset...")
    load_res = client.post("/data/load-sample", headers=headers)
    assert load_res.status_code == 200

    # 3. Mutate Company Settings (Change timezone & currency to EUR)
    print("\n[2] Explicitly Updating Company Settings (Currency: EUR, Timezone: Europe/London)...")
    comp_update = client.put("/company", headers=headers, json={
        "name": comp_name,
        "industry": "Retail/E-commerce",
        "currency": "EUR",
        "timezone": "Europe/London"
    })
    assert comp_update.status_code == 200
    assert comp_update.json()["currency"] == "EUR"
    assert comp_update.json()["timezone"] == "Europe/London"
    print("  -> PASS: Company update successful.")


    # Seed active test anomaly
    test_anomaly = client.post("/detections/test-anomaly", headers=headers)
    assert test_anomaly.status_code == 200
    anomaly_id = test_anomaly.json()["id"]
    assert test_anomaly.json()["status"] == "active"

    # 4. Generate Recommendations from active anomaly & Mutate Status
    print("\n[3] Generating Recommendations and Completing Action Item...")
    gen_rec = client.post("/recommendations/generate", headers=headers)
    assert gen_rec.status_code == 200
    recs = gen_rec.json()
    assert len(recs) > 0, "Expected at least 1 recommendation generated from active anomaly"
    target_rec = recs[0]
    rec_id = target_rec["id"]

    rec_update = client.post(f"/recommendations/{rec_id}/status?status=completed", headers=headers)
    assert rec_update.status_code == 200
    assert rec_update.json()["status"] == "completed"
    print(f"  -> PASS: Recommendation {rec_id} marked as 'completed'.")

    # Acknowledge anomaly
    ack_res = client.post(f"/detections/{anomaly_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"
    print("  -> PASS: Test anomaly acknowledged.")


    # 5. Smart Inventory Reseed and Approve Transfer
    print("\n[4] Reseeding Inventory and Approving Transfer...")
    inv_reseed = client.post("/inventory/reseed-sample", headers=headers)
    assert inv_reseed.status_code == 200
    inv_items = inv_reseed.json()["items"]
    assert len(inv_items) > 0
    target_item = inv_items[0]
    item_id = target_item["id"]
    initial_stock = target_item["current_stock"]

    transfer_res = client.post(f"/inventory/transfers/{item_id}/approve?quantity=35", headers=headers)
    assert transfer_res.status_code == 200
    assert transfer_res.json()["new_stock"] == initial_stock + 35
    print(f"  -> PASS: Stock transfer approved (+35 units: {initial_stock} -> {initial_stock + 35}).")

    # 6. Update User Profile
    print("\n[5] Updating User Profile...")
    profile_res = client.put("/auth/me", headers=headers, json={
        "full_name": "Marcus Wright Senior",
        "phone_number": "+1555999888"
    })
    assert profile_res.status_code == 200
    assert profile_res.json()["user"]["full_name"] == "Marcus Wright Senior"
    print("  -> PASS: User profile updated.")

    # 7. SIMULATE LOGOUT & RE-LOGIN (NEW SESSION)
    print("\n[6] Logging Out & Re-authenticating...")
    new_login = client.post("/auth/login", json={
        "identifier": admin_user,
        "password": "MarcusPassword123!",
        "portal_type": "admin"
    })
    assert new_login.status_code == 200
    new_token = new_login.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # 8. VERIFY ALL STATE CHANGES PERSIST AFTER RE-LOGIN
    print("\n[7] Verifying Full Persistence Across All Subsystems...")
    
    # Check Company Settings
    persisted_comp = client.get("/company", headers=new_headers).json()
    assert persisted_comp["currency"] == "EUR", f"Expected EUR, got {persisted_comp['currency']}"
    assert persisted_comp["timezone"] == "Europe/London", f"Expected Europe/London, got {persisted_comp['timezone']}"
    print("  -> PASS: Company Settings persisted (EUR, Europe/London).")

    # Check User Profile
    persisted_user = client.get("/auth/me", headers=new_headers).json()["user"]
    assert persisted_user["full_name"] == "Marcus Wright Senior"
    assert persisted_user["phone_number"] == "+1555999888"
    print("  -> PASS: User Profile persisted (Marcus Wright Senior).")

    # Check Anomaly Status
    all_detections = client.get("/detections?limit=100", headers=new_headers).json()
    persisted_det = next((d for d in all_detections if d["id"] == anomaly_id), None)
    assert persisted_det is not None
    assert persisted_det["status"] == "acknowledged"
    print(f"  -> PASS: Anomaly {anomaly_id} persisted as 'acknowledged'.")

    # Check Recommendation Status
    all_recs = client.get("/recommendations", headers=new_headers).json()
    persisted_r = next((r for r in all_recs if r["id"] == rec_id), None)
    assert persisted_r is not None
    assert persisted_r["status"] == "completed"
    print(f"  -> PASS: Recommendation {rec_id} persisted as 'completed'.")

    # Check Inventory Stock
    persisted_inv = client.get("/inventory/summary", headers=new_headers).json()
    persisted_it = next((it for it in persisted_inv["items"] if it["id"] == item_id), None)
    assert persisted_it is not None
    assert persisted_it["current_stock"] == initial_stock + 35
    print(f"  -> PASS: Inventory stock persisted at {initial_stock + 35} units.")

    print("\n" + "=" * 70)
    print("  STATE PERSISTENCE AND ROUND-TRIP MUTATIONS FULLY VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    test_full_state_persistence()
