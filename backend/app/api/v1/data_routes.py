from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import random
import io
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, Response, Query, Body, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.data_schema import IngestionResponse
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_processing_service import DataProcessingService
from app.services.company_service import CompanyService
from app.services.dataset_store import TenantDatasetStore
from app.middleware.auth_middleware import get_current_tenant_id, get_current_user, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/data", tags=["Data Ingestion & Pipeline"])


@router.post("/upload", response_model=IngestionResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    """
    Universal File Upload Handler accepting:
    - Excel spreadsheets (.xlsx, .xls, .xlsm, .xlsb)
    - Word documents (.docx) with table extraction
    - Delimited text files (.csv, .tsv, .psv, .txt)
    - Structured data (.json, .jsonl, .parquet)
    - PDF documents (.pdf)
    """
    tenant_id = current_user.company_id
    ingestion_service = DataIngestionService(tenant_id=tenant_id)
    df, filename = await ingestion_service.read_uploaded_file(file)
    
    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.process_dataframe(df, source_filename=filename)


@router.post("/ingest-raw", response_model=IngestionResponse)
async def ingest_raw_data(
    payload: dict = Body(...),
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    """
    Direct Real-Time Ingestion for Streaming, JSON, or Tabular records without uploading files.
    """
    tenant_id = current_user.company_id
    raw_records = payload.get("records") or payload.get("data") or payload
    if isinstance(raw_records, dict):
        df = pd.DataFrame([raw_records])
    elif isinstance(raw_records, list):
        df = pd.DataFrame(raw_records)
    else:
        df = pd.DataFrame()

    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.process_dataframe(df, source_filename="realtime_stream_event.json")


@router.put("/dataset", response_model=IngestionResponse)
def update_dataset(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    """
    Updates the active in-memory dataset with edited rows/columns,
    persists changes, and re-computes all analytical metrics, detections, and predictions.
    """
    tenant_id = current_user.company_id
    records = payload.get("records")
    filename = payload.get("filename", "edited_dataset.csv")
    if not records or not isinstance(records, list):
        raise HTTPException(status_code=400, detail="Invalid records payload.")

    df = pd.DataFrame(records)
    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.process_dataframe(df, source_filename=filename)


@router.get("/dataset/download")
def download_active_dataset(
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Exports the current active dataset as a CSV file download.
    """
    df = TenantDatasetStore.get_dataset(tenant_id)
    if df is None or len(df) == 0:
        raise HTTPException(status_code=404, detail="No active dataset available to download.")

    # Remove internal tracking columns
    clean_df = df.copy()
    for col in list(clean_df.columns):
        if col.startswith("_"):
            clean_df.drop(columns=[col], inplace=True)

    csv_buffer = io.StringIO()
    clean_df.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()

    meta = TenantDatasetStore.get_metadata(tenant_id) or {}
    filename = meta.get("filename", "datalyze_active_dataset.csv")
    if not filename.endswith(".csv"):
        filename = f"{filename.rsplit('.', 1)[0]}.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/load-sample", response_model=IngestionResponse)
def load_sample_dataset(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    """
    Generates a realistic 30-day historical multi-channel business dataset
    matching the company's industry profile, and runs it through the full pipeline.
    """
    tenant_id = current_user.company_id
    company_service = CompanyService(db, tenant_id=tenant_id)
    company = company_service.get_company_profile()
    industry = company.industry if company else "Retail"

    # Generate 30 days of data ending today
    end_dt = datetime.now(timezone.utc).date()
    start_dt = end_dt - timedelta(days=30)
    
    records = []
    regions = ["North", "South", "East", "West"]
    categories = ["Electronics", "Apparel", "Home & Living", "Health & Beauty"]
    channels = ["Online Store", "Mobile App", "In-Store POS", "Marketplace"]

    random.seed(42 + tenant_id)

    cur_dt = start_dt
    while cur_dt <= end_dt:
        date_str = cur_dt.strftime("%Y-%m-%d")
        day_of_week = cur_dt.weekday()
        weekend_boost = 1.35 if day_of_week in [4, 5, 6] else 1.0
        
        num_transactions = int(random.randint(15, 30) * weekend_boost)

        for i in range(num_transactions):
            reg = random.choice(regions)
            cat = random.choice(categories)
            chan = random.choice(channels)
            
            base_amount = random.uniform(25.0, 180.0)
            if cat == "Electronics":
                base_amount *= random.uniform(1.8, 3.5)
            
            days_ago = (end_dt - cur_dt).days
            if 10 <= days_ago <= 13 and reg == "East":
                base_amount *= 0.45

            qty = random.randint(1, 4)
            records.append({
                "date": date_str,
                "order_id": f"ORD-{cur_dt.strftime('%m%d')}-{random.randint(1000, 9999)}",
                "revenue": round(base_amount, 2),
                "units": qty,
                "region": reg,
                "product_category": cat,
                "sales_channel": chan,
                "visitors": random.randint(80, 150)
            })

        cur_dt += timedelta(days=1)

    df = pd.DataFrame(records)
    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.process_dataframe(df, source_filename=f"demo_{industry.lower().replace('/', '_')}_sample_30d.csv")


@router.get("/dataset/info")
@router.get("/dataset-info")
def get_dataset_info(tenant_id: int = Depends(get_current_tenant_id)):
    """
    Returns active in-memory dataset metadata, column catalog, and statistical profiling.
    """
    meta = TenantDatasetStore.get_metadata(tenant_id)
    if not meta:
        return {"has_dataset": False, "message": "No active dataset currently cached in memory."}
    return {"has_dataset": True, **meta}


@router.get("/dataset/preview")
@router.get("/dataset-preview")
def get_dataset_preview(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Returns paginated raw data rows from the active in-memory dataset.
    """
    return TenantDatasetStore.get_preview(tenant_id, limit=limit, offset=offset)


@router.post("/dataset/query")
def query_dataset(
    payload: Dict[str, Any] = Body(...),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Executes in-memory filtering, grouping, aggregation, or sorting against the active dataset.
    """
    return TenantDatasetStore.execute_query(
        tenant_id=tenant_id,
        filters=payload.get("filters"),
        group_by=payload.get("group_by"),
        agg_col=payload.get("agg_col"),
        agg_func=payload.get("agg_func", "sum"),
        sort_by=payload.get("sort_by"),
        ascending=payload.get("ascending", False),
        limit=payload.get("limit", 50)
    )


@router.get("/dataset/column/{col_name}")
def get_column_values(
    col_name: str,
    limit: int = Query(50, ge=1, le=200),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Returns distinct values and frequencies for a specific column in the active dataset.
    """
    return TenantDatasetStore.get_column_values(tenant_id, col_name=col_name, limit=limit)


@router.get("/sample-csv")
def download_sample_csv(template_type: str = Query("retail", alias="type")):
    """
    Provides downloadable CSV templates for different data schemas.
    """
    templates = {
        "retail": (
            "date,order_id,revenue,units,region,product_category,sales_channel,visitors\n"
            "2026-08-01,ORD-1001,149.99,2,North,Electronics,Online Store,120\n"
            "2026-08-01,ORD-1002,45.50,1,East,Apparel,Mobile App,85\n"
            "2026-08-01,ORD-1003,89.00,3,West,Home & Living,In-Store POS,95\n"
            "2026-08-02,ORD-1004,210.00,4,South,Electronics,Online Store,140\n"
            "2026-08-02,ORD-1005,32.00,1,North,Health & Beauty,Mobile App,110\n"
        ),
        "saas": (
            "date,mrr,churn_rate,active_users,new_signups,plan_tier,region\n"
            "2026-08-01,45200.00,1.8,1240,42,Enterprise,North America\n"
            "2026-08-02,45800.00,1.7,1255,48,Pro,Europe\n"
            "2026-08-03,46300.00,1.9,1270,39,Growth,Asia-Pacific\n"
            "2026-08-04,47100.00,1.6,1290,55,Enterprise,North America\n"
        ),
        "inventory": (
            "date,sku,product_name,stock_level,reorder_point,units_sold,warehouse\n"
            "2026-08-01,SKU-4001,Pro Ultra Sensor,85,50,12,Hub-North\n"
            "2026-08-01,SKU-4002,Industrial Cable Pack,240,80,25,Hub-West\n"
            "2026-08-02,SKU-4003,Wireless Beacon Pro,18,30,10,Hub-East\n"
            "2026-08-02,SKU-4004,Power Inverter 500W,110,40,15,Hub-South\n"
        ),
        "universal": (
            "date,transaction_id,amount,units,department,city,channel\n"
            "2026-08-01,TXN-8801,340.50,5,Sales,New York,Direct\n"
            "2026-08-01,TXN-8802,120.00,2,Support,London,Online\n"
            "2026-08-02,TXN-8803,780.25,8,Operations,Tokyo,Partner\n"
            "2026-08-02,TXN-8804,450.00,4,Engineering,Berlin,Direct\n"
        )
    }

    csv_content = templates.get(template_type, templates["retail"])
    filename = f"datalyze_{template_type}_template.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
