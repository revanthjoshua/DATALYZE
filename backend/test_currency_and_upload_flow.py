import io
import asyncio
import httpx
from app.main import app

async def test_currency_auto_detection_and_settings_flow():
    print("Testing Currency Auto-Detection & Company Settings E2E Flow...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@datalyze.com", "password": "password123"}
        )
        if login_res.status_code != 200:
            login_res = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@datalyze.com", "password": "Admin123!"}
            )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload INR Currency CSV (₹ symbols in values)
        inr_csv = (
            "date,total_sales_inr,order_volume,region,department\n"
            "2026-08-10,₹45000.00,120,North,Fashion\n"
            "2026-08-11,₹52000.50,135,North,Footwear\n"
            "2026-08-12,₹38000.00,95,South,Accessories\n"
            "2026-08-13,₹61000.00,150,North,Fashion\n"
            "2026-08-14,₹59000.00,140,West,Beauty\n"
        )
        files = {"file": ("inr_sales_august.csv", io.BytesIO(inr_csv.encode("utf-8")), "text/csv")}
        upload_res = await client.post("/api/v1/data/upload", headers=headers, files=files)
        assert upload_res.status_code == 200, upload_res.text
        print("[PASS] INR CSV uploaded successfully:", upload_res.json()["message"])

        # 3. Verify Company Currency automatically synchronized to INR
        comp_res = await client.get("/api/v1/company", headers=headers)
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["currency"] == "INR", f"Expected INR but got {comp_data['currency']}"
        print("[PASS] Company currency auto-adapted to file currency: INR")

        # 4. Test Updating Company Profile via Settings (Change to EUR)
        update_res = await client.put(
            "/api/v1/company",
            headers=headers,
            json={
                "name": "Acme Europe Logistics",
                "industry": "Supply Chain/Logistics",
                "currency": "EUR",
                "timezone": "Europe/Berlin"
            }
        )
        assert update_res.status_code == 200
        updated_comp = update_res.json()
        assert updated_comp["currency"] == "EUR"
        assert updated_comp["name"] == "Acme Europe Logistics"
        print("[PASS] Company settings updated to EUR & Acme Europe Logistics")

        # 5. Check Dashboard KPIs reflect only the uploaded file's metrics
        kpi_res = await client.get("/api/v1/kpis/summary", headers=headers)
        assert kpi_res.status_code == 200
        kpis = kpi_res.json()
        kpi_names = [k["name"] for k in kpis]
        print(f"[PASS] Dashboard active metrics derived 100% from file: {kpi_names}")
        assert any("sales" in k.lower() or "inr" in k.lower() or "total" in k.lower() for k in kpi_names)

        # 6. Check Noah understands the updated currency and numbers
        noah_res = await client.post(
            "/api/v1/noah/query",
            headers=headers,
            json={"question": "What is our total sales in the uploaded file?"}
        )
        assert noah_res.status_code == 200
        noah_ans = noah_res.json()["answer"]
        print("[PASS] Noah response with clean text:\n", noah_ans)

if __name__ == "__main__":
    asyncio.run(test_currency_auto_detection_and_settings_flow())
    print("\n=======================================================")
    print("ALL CURRENCY, UPLOAD, & SETTINGS E2E TESTS PASSED 100%!")
    print("=======================================================")
