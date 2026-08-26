import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_transfer_and_utilization():
    print("Testing Inventory Transfer Persistence & Dynamic Capacity Utilization...")

    # 1. Login/Register
    auth_res = client.post("/api/v1/auth/login", json={"email": "revanth@sns.edu", "password": "password123"})
    if auth_res.status_code != 200:
        auth_res = client.post("/api/v1/auth/register", json={
            "email": "revanth@sns.edu",
            "password": "password123",
            "full_name": "Revanth Joshua R",
            "company_name": "SNS Institutions",
            "industry": "Restaurant & Food Service"
        })
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Reseed sample inventory
    reseed_res = client.post("/api/v1/inventory/reseed", headers=headers)
    assert reseed_res.status_code == 200
    summary = reseed_res.json()

    print(f"Inventory Summary: {summary['total_items']} items, {summary['total_warehouses']} warehouses")
    
    # Verify warehouse utilizations are calculated and NOT all 25.0%
    warehouses = summary.get("warehouses", [])
    utilizations = [w["current_utilization"] for w in warehouses]
    print(f"Warehouse Capacity Utilizations: {utilizations}")
    assert not all(u == 25.0 for u in utilizations), f"Utilizations should not all be 25.0%, got: {utilizations}"

    # 3. Test Transfer Approval
    items = summary.get("items", [])
    assert len(items) > 0
    target_item = items[0]
    orig_stock = target_item["current_stock"]

    transfer_res = client.post(f"/api/v1/inventory/transfers/{target_item['id']}/approve?quantity=35", headers=headers)
    assert transfer_res.status_code == 200
    trans_data = transfer_res.json()
    print(f"Transfer Response: {trans_data}")
    assert trans_data["status"] == "success"

    # 4. Fetch fresh summary and verify persisted stock increase
    fresh_summary_res = client.get("/api/v1/inventory/summary", headers=headers)
    assert fresh_summary_res.status_code == 200
    fresh_summary = fresh_summary_res.json()
    fresh_item = next(it for it in fresh_summary["items"] if it["id"] == target_item["id"])
    
    print(f"Item Stock: before={orig_stock}, after={fresh_item['current_stock']}")
    assert fresh_item["current_stock"] == orig_stock + 35, "Stock was not persisted in database!"
    print("[PASS] Smart Inventory Transfer & Dynamic Utilization 100% Verified!")

if __name__ == "__main__":
    test_transfer_and_utilization()
