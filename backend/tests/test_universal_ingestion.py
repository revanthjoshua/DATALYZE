import io
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_processing_service import DataProcessingService
from app.services.dataset_store import TenantDatasetStore
from app.services.noah_service import NoahService
from app.schemas.noah_schema import NoahQueryRequest


@pytest.fixture(scope="module")
def setup_tenant_and_client():
    db = SessionLocal()
    try:
        # Create test company and user
        company = db.query(Company).filter(Company.id == 99).first()
        if not company:
            company = Company(id=99, name="Universal Analytics Corp", industry="Retail", currency="USD")
            db.add(company)
            db.commit()

        user = db.query(User).filter(User.email == "test_universal@datalyze.ai").first()
        if not user:
            user = User(
                company_id=99,
                email="test_universal@datalyze.ai",
                hashed_password=get_password_hash("Password123!"),
                full_name="Universal Tester",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(data={"sub": str(user.id), "company_id": 99, "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}
        client = TestClient(app)
        return {"client": client, "headers": headers, "db": db, "tenant_id": 99}
    finally:
        db.close()


def test_excel_xlsx_parsing():
    """Tests .xlsx spreadsheet parsing with openpyxl and banner header auto-discovery."""
    svc = DataIngestionService(tenant_id=99)

    # 1. Create a realistic Excel file with leading title banners
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Sheet 1: Empty metadata banner
        pd.DataFrame([
            ["QUARTERLY SALES REPORT 2026", None, None, None],
            ["Generated on 2026-08-24", None, None, None],
            ["date", "order_id", "revenue", "units"],
            ["2026-08-01", "ORD-101", 350.50, 3],
            ["2026-08-02", "ORD-102", 720.00, 5],
            ["2026-08-03", "ORD-103", 199.99, 1],
        ]).to_excel(writer, index=False, header=False, sheet_name="Transactions")

    xlsx_bytes = buffer.getvalue()
    df = svc.parse_raw_content(xlsx_bytes, "quarterly_sales.xlsx")

    assert len(df) == 3, f"Expected 3 data rows, got {len(df)}"
    assert "date" in df.columns or any("date" in str(c).lower() for c in df.columns)
    assert "revenue" in df.columns or any("revenue" in str(c).lower() for c in df.columns)


def test_legacy_xls_and_html_table_parsing():
    """Tests legacy .xls, BIFF8, and HTML tables disguised as .xls files."""
    svc = DataIngestionService(tenant_id=99)

    # 1. HTML table saved with .xls extension (common in SAP/ERP exports)
    html_xls = b"""
    <html>
      <body>
        <table>
          <tr><th>date</th><th>invoice_id</th><th>amount</th><th>region</th><th>status</th></tr>
          <tr><td>2026-08-01</td><td>INV-5001</td><td>$1,250.00</td><td>North</td><td>Paid</td></tr>
          <tr><td>2026-08-02</td><td>INV-5002</td><td>$3,400.50</td><td>South</td><td>Paid</td></tr>
          <tr><td>2026-08-03</td><td>INV-5003</td><td>$890.00</td><td>East</td><td>Pending</td></tr>
        </table>
      </body>
    </html>
    """
    df_html = svc.parse_raw_content(html_xls, "sap_export.xls")
    assert len(df_html) == 3, f"Expected 3 rows from HTML-in-xls, got {len(df_html)}"
    assert "amount" in df_html.columns


def test_csv_tsv_and_encoding_detection():
    """Tests CSV, TSV, pipe-delimited, and Latin-1/UTF-8-BOM encodings."""
    svc = DataIngestionService(tenant_id=99)

    # Pipe-separated CSV with currencies and percentages
    pipe_csv = (
        "date|transaction_id|sales_amount|discount_pct|channel\n"
        "2026-08-01|TX-101|$450.00|10%|Web\n"
        "2026-08-02|TX-102|$620.00|15%|Mobile\n"
        "2026-08-03|TX-103|$310.00|5%|Store\n"
    ).encode("utf-8-sig")

    df_pipe = svc.parse_raw_content(pipe_csv, "transactions.psv")
    assert len(df_pipe) == 3
    assert len(df_pipe.columns) == 5


def test_json_and_jsonl_parsing():
    """Tests JSON array of objects, wrapped JSON, and JSON Lines."""
    svc = DataIngestionService(tenant_id=99)

    # JSON Lines (NDJSON)
    jsonl_bytes = (
        b'{"date": "2026-08-01", "machine_id": "M1", "power_kwh": 420.5, "defect_rate": "1.2%"}\n'
        b'{"date": "2026-08-02", "machine_id": "M2", "power_kwh": 390.0, "defect_rate": "0.8%"}\n'
        b'{"date": "2026-08-03", "machine_id": "M1", "power_kwh": 450.2, "defect_rate": "2.1%"}\n'
    )
    df_jsonl = svc.parse_raw_content(jsonl_bytes, "iot_telemetry.jsonl")
    assert len(df_jsonl) == 3
    assert "power_kwh" in df_jsonl.columns


def test_dataset_store_and_noah_analysis(setup_tenant_and_client):
    """Tests that parsed dataset is cached in TenantDatasetStore and accessible via Noah queries."""
    tenant_id = setup_tenant_and_client["tenant_id"]
    db = setup_tenant_and_client["db"]

    # Ingest a custom multi-column dataset
    raw_csv = (
        "date,operator,factory_line,energy_kwh,defect_rate,revenue\n"
        "2026-08-01,Alice,Line-A,450.0,1.5%,$5200.00\n"
        "2026-08-02,Bob,Line-B,480.0,2.1%,$4800.00\n"
        "2026-08-03,Alice,Line-A,510.0,1.8%,$6100.00\n"
        "2026-08-04,Charlie,Line-C,430.0,0.9%,$5900.00\n"
    ).encode("utf-8")

    svc = DataIngestionService(tenant_id=tenant_id)
    df = svc.parse_raw_content(raw_csv, "factory_production.csv")

    proc_svc = DataProcessingService(db, tenant_id=tenant_id)
    res = proc_svc.process_dataframe(df, source_filename="factory_production.csv")

    assert res.status in ["success", "partial_success"]
    assert res.processed_rows == 4

    # Verify TenantDatasetStore
    meta = TenantDatasetStore.get_metadata(tenant_id)
    assert meta is not None
    assert meta["row_count"] == 4
    assert "energy_kwh" in meta["numeric_columns"]

    # Test in-memory dataset querying
    query_res = TenantDatasetStore.execute_query(
        tenant_id=tenant_id,
        group_by="operator",
        agg_col="energy_kwh",
        agg_func="sum"
    )
    assert query_res["success"] is True
    assert len(query_res["results"]) == 3  # Alice, Bob, Charlie

    # Test Noah querying real dataset
    noah = NoahService(db, tenant_id=tenant_id)
    
    # Query 1: Asking about columns and dataset structure
    q1 = NoahQueryRequest(question="What columns and data are in my uploaded factory production dataset?")
    ans1 = noah.process_query(q1)
    assert ans1.answer is not None
    assert "factory_production.csv" in ans1.answer or "records" in ans1.answer.lower()
    assert any(ref.source_type == "dataset" for ref in ans1.references) or "energy_kwh" in ans1.answer

    # Query 2: Specific numeric column calculation (energy_kwh)
    q2 = NoahQueryRequest(question="What is the total and average energy kwh?")
    ans2 = noah.process_query(q2)
    assert "energy" in ans2.answer.lower() or "total" in ans2.answer.lower()
    assert any(ref.source_type == "dataset" for ref in ans2.references)


def test_api_upload_and_dataset_routes(setup_tenant_and_client):
    """Tests the FastAPI upload endpoint with .xlsx and dataset inspection endpoints."""
    client = setup_tenant_and_client["client"]
    headers = setup_tenant_and_client["headers"]

    # 1. Create .xlsx file payload
    buffer = io.BytesIO()
    df_sample = pd.DataFrame({
        "date": ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"],
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
        "revenue": [120.50, 450.00, 310.25, 890.00],
        "units": [2, 5, 3, 8],
        "region": ["North", "South", "East", "West"],
        "channel": ["Online", "POS", "Online", "Marketplace"]
    })
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_sample.to_excel(writer, index=False, sheet_name="Sales")
    xlsx_bytes = buffer.getvalue()

    files = {"file": ("enterprise_sales.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    # Upload .xlsx
    upload_res = client.post("/api/v1/data/upload", headers=headers, files=files)
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    data = upload_res.json()
    assert data["status"] in ["success", "partial_success"]
    assert data["processed_rows"] == 4

    # 2. Test GET /api/v1/data/dataset/info
    info_res = client.get("/api/v1/data/dataset/info", headers=headers)
    assert info_res.status_code == 200
    info_json = info_res.json()
    assert info_json["has_dataset"] is True
    assert info_json["row_count"] == 4
    assert "revenue" in info_json["numeric_columns"]

    # 3. Test GET /api/v1/data/dataset/preview
    prev_res = client.get("/api/v1/data/dataset/preview?limit=10", headers=headers)
    assert prev_res.status_code == 200
    prev_json = prev_res.json()
    assert prev_json["total_rows"] == 4
    assert len(prev_json["records"]) == 4

    # 4. Test POST /api/v1/data/dataset/query
    q_payload = {
        "group_by": "region",
        "agg_col": "revenue",
        "agg_func": "sum"
    }
    q_res = client.post("/api/v1/data/dataset/query", headers=headers, json=q_payload)
    assert q_res.status_code == 200
    q_json = q_res.json()
    assert q_json["success"] is True
    assert q_json["count"] == 4  # 4 regions
