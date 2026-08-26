import pytest


def test_tenant_isolation_strict_boundary(client):
    # 1. Register Tenant A (Retail)
    res_a = client.post("/api/v1/auth/register", json={
        "email": "owner@tenanta.com",
        "password": "Password123!",
        "full_name": "Alice Admin",
        "company_name": "Tenant A Retail",
        "industry": "Retail/E-commerce"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    company_a_id = res_a.json()["company"]["id"]

    # 2. Register Tenant B (SaaS)
    res_b = client.post("/api/v1/auth/register", json={
        "email": "owner@tenantb.com",
        "password": "Password123!",
        "full_name": "Bob Admin",
        "company_name": "Tenant B Cloud",
        "industry": "SaaS/Subscription"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    company_b_id = res_b.json()["company"]["id"]

    assert company_a_id != company_b_id

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Verify both tenants start with 0 KPIs before any file is uploaded (Zero Dummy Data)
    kpis_a_initial = client.get("/api/v1/kpis", headers=headers_a).json()
    kpis_b_initial = client.get("/api/v1/kpis", headers=headers_b).json()
    assert len(kpis_a_initial) == 0
    assert len(kpis_b_initial) == 0

    # 4. Ingest real dataset into Tenant A
    load_res_a = client.post("/api/v1/data/load-sample", headers=headers_a)
    assert load_res_a.status_code == 200
    assert load_res_a.json()["status"] in ["success", "partial_success"]

    # 5. Check KPI summary for Tenant A now has calculated numbers from uploaded dataset
    summary_a = client.get("/api/v1/kpis/summary", headers=headers_a).json()
    assert len(summary_a) > 0
    rev_a = summary_a[0]
    assert rev_a["current_value"] is not None
    assert rev_a["current_value"] > 0

    # 6. CRITICAL SECURITY CHECK: Check KPI summary for Tenant B has ZERO data leaked from Tenant A
    summary_b = client.get("/api/v1/kpis/summary", headers=headers_b).json()
    assert len(summary_b) == 0

    # 7. CRITICAL SECURITY CHECK: Tenant B cannot query Tenant A's KPI values by ID
    kpi_a_id = rev_a["id"]
    forbidden_res = client.get(f"/api/v1/kpis/{kpi_a_id}/values", headers=headers_b)
    # Must return 404 because KPI does not belong to Tenant B
    assert forbidden_res.status_code == 404


def test_data_upload_and_validation(client):
    # Register a new company
    reg = client.post("/api/v1/auth/register", json={
        "email": "data@store.com",
        "password": "Password123!",
        "full_name": "Dana Manager",
        "company_name": "Dana Store",
        "industry": "Retail/E-commerce"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload valid CSV
    csv_data = (
        "date,order_id,revenue,units,region,product_category,sales_channel,visitors\n"
        "2026-08-01,ORD-1,100.0,2,North,Electronics,Online Store,50\n"
        "2026-08-01,ORD-2,200.0,3,South,Apparel,Mobile App,60\n"
        "2026-08-02,ORD-3,300.0,4,East,Home & Living,In-Store POS,70\n"
    )
    files = {"file": ("sales.csv", csv_data, "text/csv")}
    upload_res = client.post("/api/v1/data/upload", headers=headers, files=files)
    assert upload_res.status_code == 200
    res_json = upload_res.json()
    assert res_json["status"] == "success"
    assert res_json["processed_rows"] == 3
    assert res_json["validation_summary"]["is_valid"] is True

    # Verify summary cards updated
    summary = client.get("/api/v1/kpis/summary", headers=headers).json()
    rev_kpi = next(k for k in summary if k["key"] == "revenue")
    assert rev_kpi["current_value"] == 300.0  # 2026-08-02 value
    assert rev_kpi["previous_value"] == 300.0  # 2026-08-01 total (100 + 200)
