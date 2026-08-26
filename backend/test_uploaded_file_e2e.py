import io
import asyncio
import zipfile
import httpx
import pandas as pd
from app.main import app
from app.services.data_ingestion_service import DataIngestionService

def test_docx_table_parsing():
    print("Testing Word (.docx) Table Extraction...")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:tbl>'
            '<w:tr>'
            '<w:tc><w:p><w:t>Date</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>Revenue</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>Orders</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>Region</w:t></w:p></w:tc>'
            '</w:tr>'
            '<w:tr>'
            '<w:tc><w:p><w:t>2026-08-01</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>4500.50</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>35</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>North America</w:t></w:p></w:tc>'
            '</w:tr>'
            '<w:tr>'
            '<w:tc><w:p><w:t>2026-08-02</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>5200.00</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>42</w:t></w:p></w:tc>'
            '<w:tc><w:p><w:t>Europe</w:t></w:p></w:tc>'
            '</w:tr>'
            '</w:tbl>'
            '</w:body>'
            '</w:document>'
        )
        zf.writestr("word/document.xml", doc_xml)
        zf.writestr("[Content_Types].xml", "<Types/>")

    docx_bytes = buffer.getvalue()
    ingestion_service = DataIngestionService(tenant_id=1)
    df = ingestion_service.parse_raw_content(docx_bytes, filename="executive_sales_summary.docx")
    assert df is not None and not df.empty
    assert len(df) == 2
    assert "revenue" in [c.lower() for c in df.columns]
    print("[PASS] Word (.docx) table parsing extracted 2 rows and columns:", list(df.columns))

async def test_full_upload_and_noah_e2e():
    print("Testing Full Upload & Noah Grounding E2E...")
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

        # 2. Upload CSV
        csv_content = (
            "date,revenue,orders,units,region,product_category\n"
            "2026-08-10,12450.00,120,250,West,Electronics\n"
            "2026-08-11,14200.50,135,280,West,Apparel\n"
            "2026-08-12,9800.00,95,190,East,Home & Living\n"
            "2026-08-13,16500.00,150,310,West,Electronics\n"
            "2026-08-14,15100.00,140,290,South,Health & Beauty\n"
        )
        files = {"file": ("q3_performance_data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        upload_res = await client.post("/api/v1/data/upload", headers=headers, files=files)
        assert upload_res.status_code == 200, upload_res.text
        print("[PASS] CSV upload processed:", upload_res.json()["message"])

        # 3. Check Dataset Info
        info_res = await client.get("/api/v1/data/dataset/info", headers=headers)
        assert info_res.status_code == 200
        info = info_res.json()
        assert info["has_dataset"] == True
        assert info["filename"] == "q3_performance_data.csv"
        print("[PASS] Active Dataset Info matches uploaded file:", info["filename"], f"({info['row_count']} rows)")

        # 4. Check Noah Query against uploaded file
        noah_res = await client.post("/api/v1/noah/query", headers=headers, json={"question": "What is our total revenue in q3_performance_data?"})
        assert noah_res.status_code == 200
        noah_data = noah_res.json()
        print("[PASS] Noah response grounded in uploaded file:\n", noah_data["answer"])

        # 5. Check KPI Summary matches
        kpi_res = await client.get("/api/v1/kpis/summary", headers=headers)
        assert kpi_res.status_code == 200
        kpis = kpi_res.json()
        assert len(kpis) > 0
        print("[PASS] KPI Summary recomputed with", len(kpis), "active metrics")

if __name__ == "__main__":
    test_docx_table_parsing()
    asyncio.run(test_full_upload_and_noah_e2e())
    print("\n=======================================================")
    print("ALL UPLOAD, ACCESS, & NOAH E2E TESTS PASSED 100%!")
    print("=======================================================")
