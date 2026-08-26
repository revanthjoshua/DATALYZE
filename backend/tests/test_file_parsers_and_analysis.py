import io
import json
import pytest
import pandas as pd
import numpy as np
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
def setup_test_env():
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == 88).first()
        if not company:
            company = Company(id=88, name="Global Test Enterprise", industry="Retail", currency="USD")
            db.add(company)
            db.commit()

        user = db.query(User).filter(User.email == "tester_parser@datalyze.ai").first()
        if not user:
            user = User(
                company_id=88,
                email="tester_parser@datalyze.ai",
                hashed_password=get_password_hash("Password123!"),
                full_name="Parser Test Lead",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(data={"sub": str(user.id), "company_id": 88, "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}
        client = TestClient(app)
        return {"client": client, "headers": headers, "db": db, "tenant_id": 88}
    finally:
        db.close()


def test_excel_xlsx_with_formulas_and_banners():
    """Test modern Excel workbook with title banner, computed values, and currency strings."""
    svc = DataIngestionService(tenant_id=88)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        raw = [
            ["EXECUTIVE FINANCIAL SUMMARY 2026", None, None, None, None],
            ["Generated on 2026-08-24 by Finance Department", None, None, None, None],
            [None, None, None, None, None],
            ["Date", "Order ID", "Revenue", "Units Sold", "Region"],
            ["2026-08-01", "ORD-101", "$1,450.00", 10, "North"],
            ["2026-08-02", "ORD-102", "$2,100.50", 15, "South"],
            ["2026-08-03", "ORD-103", "$890.00", 6, "East"],
            ["2026-08-04", "ORD-104", "$3,400.00", 22, "West"],
            ["Total", None, "$7,840.50", 53, None]  # Trailing summary row to test stripping
        ]
        pd.DataFrame(raw).to_excel(writer, index=False, header=False, sheet_name="Monthly Sales")

    xlsx_bytes = buffer.getvalue()
    df = svc.parse_raw_content(xlsx_bytes, "financial_summary.xlsx")

    assert len(df) == 4, f"Expected 4 data rows, got {len(df)}"
    assert "Date" in df.columns or "date" in [c.lower() for c in df.columns]
    assert "Revenue" in df.columns or "revenue" in [c.lower() for c in df.columns]
    assert "Units Sold" in df.columns or "units_sold" in [c.lower() for c in df.columns]


def test_excel_multi_sheet_selection():
    """Test Excel workbook where sheet 1 is empty notes and sheet 2 is populated transactions."""
    svc = DataIngestionService(tenant_id=88)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Sheet 1: Empty or notes
        pd.DataFrame([["Instructions", "Please review sheet 2 for transactions"]]).to_excel(
            writer, index=False, header=False, sheet_name="Readme"
        )
        # Sheet 2: Main table
        pd.DataFrame({
            "Transaction_ID": ["TXN-01", "TXN-02", "TXN-03"],
            "Amount": [120.0, 450.0, 310.0],
            "Channel": ["Online", "In-Store", "Mobile"]
        }).to_excel(writer, index=False, sheet_name="DataSheet")

    xlsx_bytes = buffer.getvalue()
    df = svc.parse_raw_content(xlsx_bytes, "multi_sheet.xlsx")

    assert len(df) == 3
    assert any("amount" in c.lower() for c in df.columns)


def test_csv_with_comment_headers_and_semicolons():
    """Test European CSV with semicolon delimiters and leading comment metadata."""
    svc = DataIngestionService(tenant_id=88)

    csv_data = (
        "# ERP Report Export\n"
        "# Date: 2026-08-24\n"
        "# Currency: EUR\n"
        "date;invoice_no;sales_amount;tax_rate;country\n"
        "2026-08-01;INV-8001;€1.250,50;19%;Germany\n"
        "2026-08-02;INV-8002;€3.400,00;19%;France\n"
        "2026-08-03;INV-8003;€890,20;21%;Spain\n"
    ).encode("utf-8")

    df = svc.parse_raw_content(csv_data, "european_sales.csv")
    assert len(df) == 3
    assert "date" in df.columns
    assert "sales_amount" in df.columns
    assert "country" in df.columns


def test_pipe_delimited_with_utf8_bom():
    """Test pipe-delimited data with UTF-8 BOM encoding."""
    svc = DataIngestionService(tenant_id=88)

    psv_data = (
        "date|sku|product_name|stock_level|reorder_point|warehouse\n"
        "2026-08-01|SKU-100|Industrial Sensor|85|40|Hub-North\n"
        "2026-08-02|SKU-200|Fiber Transceiver|12|30|Hub-East\n"
        "2026-08-03|SKU-300|Power Regulator|150|50|Hub-South\n"
    ).encode("utf-8-sig")

    df = svc.parse_raw_content(psv_data, "inventory.psv")
    assert len(df) == 3
    assert "sku" in df.columns
    assert "stock_level" in df.columns


def test_json_and_jsonl_ingestion():
    """Test JSON nested structure and JSON lines."""
    svc = DataIngestionService(tenant_id=88)

    # 1. Wrapped dictionary array
    wrapped_json = json.dumps({
        "status": "ok",
        "data": [
            {"date": "2026-08-01", "revenue": 500.0, "units": 5, "region": "North"},
            {"date": "2026-08-02", "revenue": 800.0, "units": 8, "region": "South"}
        ]
    }).encode("utf-8")
    df_json = svc.parse_raw_content(wrapped_json, "wrapped.json")
    assert len(df_json) == 2
    assert "revenue" in df_json.columns

    # 2. JSONL
    jsonl_bytes = (
        b'{"date": "2026-08-01", "power_kwh": 350.2, "machine_id": "M1"}\n'
        b'{"date": "2026-08-02", "power_kwh": 410.8, "machine_id": "M2"}\n'
    )
    df_jsonl = svc.parse_raw_content(jsonl_bytes, "telemetry.jsonl")
    assert len(df_jsonl) == 2
    assert "power_kwh" in df_jsonl.columns


def test_full_pipeline_processing_and_in_memory_querying(setup_test_env):
    """Test full pipeline execution: parsing -> normalization -> TenantDatasetStore -> Noah Q&A."""
    tenant_id = setup_test_env["tenant_id"]
    db = setup_test_env["db"]

    # Ingest a rich dataset
    raw_csv = (
        'Date,Customer_Segment,Product_Category,Revenue,Units,Sales_Channel\n'
        '2026-08-01,Enterprise,Electronics,"$12,500.00",25,Direct Sales\n'
        '2026-08-02,SMB,Apparel,"$3,400.00",40,Online Store\n'
        '2026-08-03,Enterprise,Electronics,"$8,900.00",18,Direct Sales\n'
        '2026-08-04,Consumer,Home & Living,"$1,850.50",12,Mobile App\n'
        '2026-08-05,SMB,Electronics,"$5,200.00",10,Marketplace\n'
    ).encode("utf-8")

    svc = DataIngestionService(tenant_id=tenant_id)
    df = svc.parse_raw_content(raw_csv, "enterprise_orders.csv")

    proc_svc = DataProcessingService(db, tenant_id=tenant_id)
    ingest_res = proc_svc.process_dataframe(df, source_filename="enterprise_orders.csv")

    assert ingest_res.status in ["success", "partial_success"]
    assert ingest_res.processed_rows == 5

    # Verify TenantDatasetStore state
    dataset_df = TenantDatasetStore.get_dataset(tenant_id)
    assert dataset_df is not None
    assert len(dataset_df) == 5

    meta = TenantDatasetStore.get_metadata(tenant_id)
    assert meta is not None
    assert meta["row_count"] == 5
    assert "revenue" in meta["numeric_columns"]
    assert "units" in meta["numeric_columns"]

    # Verify Preview
    preview = TenantDatasetStore.get_preview(tenant_id, limit=3)
    assert preview["total_rows"] == 5
    assert len(preview["records"]) == 3
    assert preview["records"][0]["revenue"] == 12500.0

    # Verify Execute Query - Group By Category with Sum of Revenue
    query_res = TenantDatasetStore.execute_query(
        tenant_id=tenant_id,
        group_by="product_category",
        agg_col="revenue",
        agg_func="sum"
    )
    assert query_res["success"] is True
    assert len(query_res["results"]) == 3  # Electronics, Apparel, Home & Living
    # Electronics: 12500 + 8900 + 5200 = 26600
    elec_item = next(r for r in query_res["results"] if r["product_category"] == "Electronics")
    assert elec_item["sum_revenue"] == 26600.0

    # Verify Noah natural language query against real dataset in memory
    noah = NoahService(db, tenant_id=tenant_id)
    
    # 1. Total revenue query
    q1 = NoahQueryRequest(question="What is our total revenue and sales breakdown?")
    ans1 = noah.process_query(q1)
    assert "31,850.50" in ans1.answer or "revenue" in ans1.answer.lower()
    assert any(ref.source_type == "dataset" for ref in ans1.references)

    # 2. Specific segment query
    q2 = NoahQueryRequest(question="How is Enterprise segment performing?")
    ans2 = noah.process_query(q2)
    assert "enterprise" in ans2.answer.lower()
    assert any(ref.source_type == "dataset" for ref in ans2.references) or "rows" in ans2.answer.lower()


def test_api_upload_endpoint(setup_test_env):
    """Test FastAPI /api/v1/data/upload endpoint with an Excel file."""
    client = setup_test_env["client"]
    headers = setup_test_env["headers"]

    buffer = io.BytesIO()
    df_sample = pd.DataFrame({
        "date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        "order_id": ["O-1", "O-2", "O-3"],
        "revenue": [500.0, 750.0, 1200.0],
        "units": [4, 6, 10],
        "region": ["North", "South", "East"]
    })
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_sample.to_excel(writer, index=False, sheet_name="Q3_Sales")
    xlsx_content = buffer.getvalue()

    files = {"file": ("q3_sales.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/v1/data/upload", headers=headers, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] in ["success", "partial_success"]
    assert res_data["processed_rows"] == 3
    assert len(res_data["validation_summary"]["columns_detected"]) >= 5
