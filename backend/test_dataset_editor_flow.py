import io
import asyncio
import httpx
from app.main import app

async def test_dataset_editor_and_industry_expansion_flow():
    print("Testing Interactive Dataset Editor, Cell Updates, & Industry Expansion Flow...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Register unique test admin
        import time
        suffix = str(int(time.time()))
        reg_res = await client.post(
            "/api/v1/auth/register-admin",
            json={
                "email": f"admin_ed_{suffix}@datalyze.com",
                "username": f"admin_ed_{suffix}",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "full_name": "Admin User",
                "phone_number": f"+1555{suffix[-4:]}1",
                "company_name": f"Restaurant Corp {suffix}",
                "industry": "Restaurant/F&B"
            }
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload initial Restaurant CSV
        initial_csv = (
            "dish_name,unit_price,quantity,discount,customer_rating\n"
            "Paneer Butter Masala,₹290.00,4,0.05,4.8\n"
            "Chicken Biryani,₹380.00,6,0.10,4.9\n"
            "Butter Naan,₹60.00,12,0.00,4.5\n"
        )
        files = {"file": ("restaurant_menu.csv", io.BytesIO(initial_csv.encode("utf-8")), "text/csv")}
        upload_res = await client.post("/api/v1/data/upload", headers=headers, files=files)
        assert upload_res.status_code == 200
        print("[PASS] Initial dataset uploaded successfully:", upload_res.json()["message"])

        # 3. Verify Initial Metric Summary
        kpi_res1 = await client.get("/api/v1/kpis/summary", headers=headers)
        assert kpi_res1.status_code == 200
        kpis1 = kpi_res1.json()
        price_kpi1 = next(k for k in kpis1 if "price" in k["name"].lower())
        print(f"[PASS] Initial Unit Price sum = {price_kpi1['current_value']} across {len(price_kpi1['recent_history'])} rows")
        assert sum(h['value'] for h in price_kpi1['recent_history']) == 730.0  # 290 + 380 + 60

        # 4. Perform Live Spreadsheet Row Editing via PUT /api/v1/data/dataset
        edited_records = [
            {"dish_name": "Paneer Butter Masala", "unit_price": 320.0, "quantity": 5, "discount": 0.05, "customer_rating": 4.8},
            {"dish_name": "Chicken Biryani", "unit_price": 420.0, "quantity": 8, "discount": 0.10, "customer_rating": 4.9},
            {"dish_name": "Butter Naan", "unit_price": 70.0, "quantity": 15, "discount": 0.00, "customer_rating": 4.5},
            {"dish_name": "Tandoori Platter (New)", "unit_price": 750.0, "quantity": 3, "discount": 0.15, "customer_rating": 5.0},
        ]
        edit_res = await client.put(
            "/api/v1/data/dataset",
            headers=headers,
            json={"records": edited_records, "filename": "restaurant_menu_edited.csv"}
        )
        assert edit_res.status_code == 200
        print("[PASS] Dataset successfully edited and re-ingested:", edit_res.json()["message"])

        # 5. Verify that Dashboard KPIs immediately reflect the edited cell values & new row
        kpi_res2 = await client.get("/api/v1/kpis/summary", headers=headers)
        assert kpi_res2.status_code == 200
        kpis2 = kpi_res2.json()
        print("DEBUG kpis2 names:", [k["name"] for k in kpis2])
        price_kpi2 = next((k for k in kpis2 if "price" in k["name"].lower()), None)
        assert price_kpi2 is not None, f"Price KPI not found in {[k['name'] for k in kpis2]}"
        print(f"[PASS] Updated Unit Price sum = {sum(h['value'] for h in price_kpi2['recent_history'])} across {len(price_kpi2['recent_history'])} rows")
        assert sum(h['value'] for h in price_kpi2['recent_history']) == 1560.0  # 320 + 420 + 70 + 750
        assert len(price_kpi2['recent_history']) == 4

        # 6. Test CSV Export Endpoint
        download_res = await client.get("/api/v1/data/dataset/download", headers=headers)
        assert download_res.status_code == 200
        csv_text = download_res.text
        assert "Tandoori Platter (New)" in csv_text
        print("[PASS] Active edited dataset successfully downloaded as CSV!")

        # 7. Update Industry to one of the newly added types (e.g. Restaurants/F&B)
        ind_res = await client.put(
            "/api/v1/company",
            headers=headers,
            json={"name": "Royal Spice Dine", "industry": "Restaurants/F&B", "currency": "INR", "timezone": "Asia/Kolkata"}
        )
        assert ind_res.status_code == 200
        assert ind_res.json()["industry"] == "Restaurants/F&B"
        print("[PASS] Company industry updated to Restaurants/F&B successfully!")

if __name__ == "__main__":
    asyncio.run(test_dataset_editor_and_industry_expansion_flow())
    print("\n=================================================================")
    print("ALL DATASET EDITOR, EYE VIEWER, & INDUSTRY TESTS PASSED 100%!")
    print("=================================================================")
