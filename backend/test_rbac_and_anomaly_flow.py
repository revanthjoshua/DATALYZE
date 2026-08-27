import asyncio
import httpx
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.inventory_item import InventoryItem
from app.models.warehouse_location import WarehouseLocation
from app.core.security import hash_password

async def test_rbac_and_anomaly_flow():
    print("Testing RBAC Security, Anomaly Endpoints, Dynamic Forecasts, and Inventory Transfer...")
    
    # 1. Seed Viewer User & Inventory item in DB for test
    db = SessionLocal()
    try:
        company = db.query(Company).first()
        if not company:
            company = Company(name="Test Corp", industry="Retail/E-commerce", currency="USD")
            db.add(company)
            db.commit()
            db.refresh(company)

        viewer = db.query(User).filter(User.email == "viewer@datalyze.com").first()
        if not viewer:
            viewer = User(
                email="viewer@datalyze.com",
                hashed_password=hash_password("Viewer123!"),
                full_name="Test Viewer",
                role="viewer",
                company_id=company.id,
                is_active=True
            )
            db.add(viewer)

        admin = db.query(User).filter(User.email == "admin@datalyze.com").first()
        if not admin:
            admin = User(
                email="admin@datalyze.com",
                hashed_password=hash_password("Admin123!"),
                full_name="Test Admin",
                role="company admin",
                company_id=company.id,
                is_active=True
            )
            db.add(admin)
        db.commit()

        # Seed Warehouse & Item
        wh = db.query(WarehouseLocation).filter(WarehouseLocation.company_id == company.id).first()
        if not wh:
            wh = WarehouseLocation(company_id=company.id, name="Main Hub", code="WH-1", region="Central", capacity=10000)
            db.add(wh)
            db.commit()
            db.refresh(wh)

        item = db.query(InventoryItem).filter(InventoryItem.company_id == company.id).first()
        if not item:
            item = InventoryItem(
                company_id=company.id,
                warehouse_id=wh.id,
                sku="SKU-TEST-1",
                name="Wireless Headphones",
                current_stock=10,
                reorder_point=25.0,
                cost_price=30.0,
                selling_price=60.0
            )
            db.add(item)
            db.commit()
            db.refresh(item)
        test_item_id = item.id
    finally:
        db.close()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 2. Login as Admin
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@datalyze.com", "password": "password123"}
        )
        if admin_login.status_code != 200:
            admin_login = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@datalyze.com", "password": "Admin123!"}
            )
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 3. Login as Viewer
        viewer_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@datalyze.com", "password": "Viewer123!"}
        )
        assert viewer_login.status_code == 200
        viewer_token = viewer_login.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        # 4. RBAC Test: Viewer attempts to access Admin endpoint PUT /api/v1/company
        viewer_update_res = await client.put(
            "/api/v1/company",
            headers=viewer_headers,
            json={"name": "Hacked Name"}
        )
        print(f"[RBAC CHECK] Viewer PUT /company response status: {viewer_update_res.status_code}")
        assert viewer_update_res.status_code == 403, f"Expected 403 Forbidden for Viewer, got {viewer_update_res.status_code}"
        print("[PASS] RBAC Security correctly rejected unauthorized Viewer attempt with 403 Forbidden!")

        # 5. RBAC Test: Viewer attempts to invite a user POST /api/v1/company/invite
        viewer_invite_res = await client.post(
            "/api/v1/company/invite",
            headers=viewer_headers,
            json={"email": "hacker@test.com", "role": "admin"}
        )
        assert viewer_invite_res.status_code == 403
        print("[PASS] RBAC Security correctly rejected Viewer invite attempt with 403 Forbidden!")

        # 6. Admin Test: Admin successfully invites a team member
        invite_email = f"analyst_{int(asyncio.get_event_loop().time())}@datalyze.com"
        admin_invite_res = await client.post(
            "/api/v1/company/invite",
            headers=admin_headers,
            json={"email": invite_email, "role": "analyst", "full_name": "Jordan Analyst"}
        )
        assert admin_invite_res.status_code == 201
        print(f"[PASS] Admin successfully invited new team member ({invite_email})!")

        # 7. Test Anomaly Simulation & Acknowledge All Endpoints
        test_anomaly_res = await client.post("/api/v1/detections/test-anomaly", headers=admin_headers)
        assert test_anomaly_res.status_code == 200
        det_data = test_anomaly_res.json()
        print(f"[PASS] Simulated Test Anomaly created (Severity: {det_data['severity']}, % Change: {det_data['percentage_change']}%)")

        # Acknowledge All
        ack_all_res = await client.post("/api/v1/detections/acknowledge-all", headers=admin_headers)
        assert ack_all_res.status_code == 200
        print(f"[PASS] Acknowledge All endpoint succeeded: {ack_all_res.json()['message']}")

        # 8. Test Inventory Transfer Approval
        inv_summary_res = await client.get("/api/v1/inventory/summary", headers=admin_headers)
        inv_data = inv_summary_res.json()
        if not inv_data["items"]:
            await client.post("/api/v1/inventory/reseed-sample", headers=admin_headers)
            inv_summary_res = await client.get("/api/v1/inventory/summary", headers=admin_headers)
            inv_data = inv_summary_res.json()

        assert len(inv_data["items"]) > 0
        target_item = inv_data["items"][0]
        initial_stock = target_item["current_stock"]

        transfer_res = await client.post(
            f"/api/v1/inventory/transfers/{target_item['id']}/approve?quantity=50",
            headers=admin_headers
        )
        assert transfer_res.status_code == 200
        transfer_json = transfer_res.json()
        assert transfer_json["status"] == "success"
        print(f"[PASS] Inventory transfer approved: {transfer_json['message']} (Initial stock: {initial_stock} -> +50)")

        # 9. Test Dynamic Forecast Horizon (14 Days)
        kpi_list_res = await client.get("/api/v1/kpis", headers=admin_headers)
        kpis = kpi_list_res.json()
        if kpis:
            kpi_id = kpis[0]["id"]
            forecast_14d_res = await client.get(f"/api/v1/predictions/{kpi_id}?horizon_days=14", headers=admin_headers)
            assert forecast_14d_res.status_code == 200
            preds = forecast_14d_res.json()
            assert len(preds) == 14
            print(f"[PASS] Dynamic 14-day forward forecast successfully generated ({len(preds)} daily projections)!")

if __name__ == "__main__":
    asyncio.run(test_rbac_and_anomaly_flow())
    print("\n=================================================================")
    print("ALL RBAC, ANOMALY, INVENTORY & FORECAST TESTS PASSED 100%!")
    print("=================================================================")
