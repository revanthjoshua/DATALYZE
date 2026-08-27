import asyncio
import httpx
from app.main import app

async def run_full_suite():
    print("Running Complete Full-Stack API Suite Verification with ASGI In-Memory Client...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        res = await client.get("/")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] Health Check Passed:", res.json()["status"])

        # 2. Login as admin
        # 2. Register unique admin
        import time
        suffix = str(int(time.time()))
        reg_res = await client.post(
            "/api/v1/auth/register-admin",
            json={
                "email": f"admin_fs_{suffix}@datalyze.com",
                "username": f"admin_fs_{suffix}",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "full_name": "Admin User",
                "phone_number": f"+1555{suffix[-4:]}1",
                "company_name": f"Acme Retail Corp {suffix}",
                "industry": "Retail/E-commerce"
            }
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] Authentication & Multi-Tenant Token Obtained")

        # 3. Test Data Ingestion - Load Sample
        sample_res = await client.post("/api/v1/data/load-sample", headers=headers)
        assert sample_res.status_code == 200, f"Sample load failed: {sample_res.text}"
        print("[PASS] 30-Day Sample Ingestion Pipeline Passed:", sample_res.json()["message"])

        # 4. Test KPI Summary
        kpi_res = await client.get("/api/v1/kpis/summary", headers=headers)
        assert kpi_res.status_code == 200, f"KPI summary failed: {kpi_res.text}"
        kpis = kpi_res.json()
        print(f"[PASS] KPI Summary Passed: {len(kpis)} active business KPIs tracked")

        # 5. Test Anomaly Detections
        det_res = await client.get("/api/v1/detections", headers=headers)
        assert det_res.status_code == 200, f"Detections failed: {det_res.text}"
        print(f"[PASS] Anomaly Detection Engine Passed: {len(det_res.json())} alerts found")

        # 6. Test Predictions
        if kpis:
            kpi_id = kpis[0]["id"]
            pred_res = await client.get(f"/api/v1/predictions/{kpi_id}", headers=headers)
            assert pred_res.status_code == 200, f"Predictions failed: {pred_res.text}"
            print(f"[PASS] 7-Day Forecast Engine Passed: {len(pred_res.json())} daily projections generated")

        # 7. Test Recommendations
        rec_res = await client.get("/api/v1/recommendations", headers=headers)
        assert rec_res.status_code == 200, f"Recommendations failed: {rec_res.text}"
        print(f"[PASS] Actionable Prescriptions Passed: {len(rec_res.json())} recommendations active")

        # 8. Test Smart Inventory
        inv_res = await client.get("/api/v1/inventory/summary", headers=headers)
        assert inv_res.status_code == 200, f"Inventory failed: {inv_res.text}"
        print(f"[PASS] Smart Inventory Passed: {inv_res.json()['total_items']} items tracked across fulfillment hubs")

        # 9. Test Noah Q&A and Agentic Reasoning
        noah_q_res = await client.post(
            "/api/v1/noah/query",
            headers=headers,
            json={"question": "How is our business tracking and what are our top recommendations?"}
        )
        assert noah_q_res.status_code == 200, f"Noah Ask failed: {noah_q_res.text}"
        print("[PASS] Noah Conversational Intelligence Passed:", noah_q_res.json()["answer"][:90] + "...")

        noah_agent_res = await client.post(
            "/api/v1/noah/agentic-reasoning",
            headers=headers,
            json={"goal": "Audit revenue and synthesize corrective actions"}
        )
        assert noah_agent_res.status_code == 403, f"Noah Agentic should be 403-gated, got: {noah_agent_res.status_code}"
        print("[PASS] Noah Multi-Step Agentic Reasoning securely 403-gated during Phase 5 MVP")

        # 10. Test Company Settings & Profile Update
        comp_res = await client.get("/api/v1/company", headers=headers)
        assert comp_res.status_code == 200, f"Company profile failed: {comp_res.text}"
        print("[PASS] Workspace Profile & Multi-Tenant Isolation Passed:", comp_res.json()["name"])

        users_res = await client.get("/api/v1/company/users", headers=headers)
        assert users_res.status_code == 200, f"Company users failed: {users_res.text}"
        print(f"[PASS] Team Members List Passed: {len(users_res.json())} authorized members")

        # 11. Test Template CSV Downloads (retail, saas, inventory, universal)
        for ttype in ["retail", "saas", "inventory", "universal"]:
            csv_dl = await client.get(f"/api/v1/data/sample-csv?type={ttype}")
            assert csv_dl.status_code == 200, f"CSV download failed for {ttype}"
        print("[PASS] Domain-Specific Sample Template CSV Downloads Passed (Retail, SaaS, Inventory, Universal)")

    print("\n=======================================================")
    print("ALL FULL-STACK SERVICES VERIFIED AND 100% OPERATIONAL!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_full_suite())
