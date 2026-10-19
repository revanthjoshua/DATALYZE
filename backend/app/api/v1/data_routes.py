import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import random
import io
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, Response, Query, Body, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.payload_limits import check_json_response, check_response_size
from app.schemas.data_schema import IngestionResponse
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_processing_service import DataProcessingService
from app.services.company_service import CompanyService
from app.services.dataset_store import TenantDatasetStore
from app.services.storage_service import storage_service
from app.middleware.auth_middleware import get_current_tenant_id, get_current_user, require_analyst_user
from app.models.user import User
from app.models.uploaded_dataset import UploadedDataset

logger = logging.getLogger("datalyze.data")

router = APIRouter(prefix="/data", tags=["Data Ingestion & Pipeline"])


@router.get("/capabilities")
def data_capabilities(current_user: User = Depends(get_current_user)):
    return {
        "max_upload_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
        "max_request_bytes": settings.MAX_REQUEST_SIZE_BYTES,
        "max_response_bytes": settings.MAX_RESPONSE_SIZE_BYTES,
        "editor_max_rows": 10000,
    }


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
    # An explicitly supplied envelope is authoritative, even when empty. Falling
    # back on truthiness turns {"records": []} into a bogus row and replaces data.
    raw_records = payload["records"] if "records" in payload else payload.get("data", payload)
    if isinstance(raw_records, dict):
        raw_records = [raw_records]
    if (
        not isinstance(raw_records, list)
        or not raw_records
        or any(not isinstance(record, dict) or not record for record in raw_records)
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide a non-empty record object or a non-empty array of record objects in records or data.",
        )
    df = pd.DataFrame(raw_records)

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

    dataset = db.query(UploadedDataset).filter(
        UploadedDataset.company_id == tenant_id
    ).order_by(UploadedDataset.created_at.desc()).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No active dataset to edit.")
    revision = payload.get("revision")
    if not revision:
        raise HTTPException(status_code=428, detail="Reopen the editor before saving; a complete dataset snapshot is required.")
    if revision != f"{dataset.id}:{dataset.file_hash}":
        raise HTTPException(status_code=409, detail="The dataset changed while you were editing. Reopen it to avoid overwriting newer data.")
    df = pd.DataFrame(records)
    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.process_dataframe(df, source_filename=filename, expected_revision=revision)


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


@router.delete("/dataset")
@router.delete("/delete")
@router.delete("/clear")
def delete_dataset(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    """
    Deletes the tenant's uploaded dataset, disk files, in-memory cache,
    and ALL generated analytics (KPIs, values, detections, predictions,
    recommendations, alerts, reports, inventory items, and warehouse locations).
    """
    tenant_id = current_user.company_id
    processing_service = DataProcessingService(db, tenant_id=tenant_id)
    return processing_service.delete_active_dataset()


def _ensure_dataset_loaded(tenant_id: int, db: Session) -> Optional[pd.DataFrame]:
    """
    Ensures active dataset is restored into in-memory TenantDatasetStore
    from persistent storage_service / database across serverless cold starts.
    """
    dataset = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.company_id == tenant_id)
        .order_by(UploadedDataset.created_at.desc())
        .first()
    )
    if not dataset:
        TenantDatasetStore.clear_dataset(tenant_id)
        return None

    current_revision=f'{dataset.id}:{dataset.file_hash}'
    metadata=TenantDatasetStore.get_metadata(tenant_id)
    if metadata and metadata.get('revision')==current_revision:
        return TenantDatasetStore.get_dataset(tenant_id)
    TenantDatasetStore.clear_dataset(tenant_id)

    file_bytes = None
    if dataset.storage_path:
        try:
            file_bytes = storage_service.get_dataset(
                tenant_id=tenant_id,
                storage_key=dataset.storage_path,
                db=db
            )
        except Exception as e:
            logger.warning(f"Error fetching dataset bytes for tenant #{tenant_id}: {e}")

    if file_bytes:
        try:
            ingestion = DataIngestionService(tenant_id=tenant_id)
            df_restored = pd.read_csv(io.BytesIO(file_bytes), keep_default_na=False, na_values=[''], dtype={
                item["name"]: str for item in (dataset.schema_metadata or [])
                if item.get("data_type") in ["Identifier", "Text", "Categorical"]
            })
            TenantDatasetStore.set_dataset(
                tenant_id=tenant_id,
                df=df_restored,
                source_filename=dataset.filename,
                detected_profile=dataset.detected_profile,
                revision=current_revision
            )
            return df_restored
        except Exception as e:
            logger.error(f"Error parsing restored dataset for tenant #{tenant_id}: {e}", exc_info=True)

    return None


@router.get("/dataset/info")
@router.get("/dataset-info")
def get_dataset_info(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Returns active dataset metadata, column catalog, and statistical profiling.
    Restores from persistent database and disk storage if in-memory cache was cleared.
    """
    _ensure_dataset_loaded(tenant_id, db)
    meta = TenantDatasetStore.get_metadata(tenant_id)

    if not meta:
        return {"has_dataset": False, "message": "No active dataset currently uploaded."}
    return {"has_dataset": True, **meta}


@router.get("/dataset/editor")
def get_editor_snapshot(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    tenant_id = current_user.company_id
    dataset = db.query(UploadedDataset).filter(
        UploadedDataset.company_id == tenant_id
    ).order_by(UploadedDataset.created_at.desc()).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No active dataset to edit.")
    # Restore current durable data rather than returning another worker's stale cache.
    TenantDatasetStore.clear_dataset(tenant_id)
    df = _ensure_dataset_loaded(tenant_id, db)
    if df is None:
        raise HTTPException(status_code=409, detail="Dataset could not be loaded. Editing is unavailable.")
    if len(df) > 10000:
        raise HTTPException(status_code=413, detail="The spreadsheet editor supports up to 10,000 rows. Download this dataset to edit it and upload the complete result.")
    public = df[[c for c in df.columns if not str(c).startswith("_")]]
    snapshot = {
        "records": json.loads(public.to_json(orient="records", date_format="iso", double_precision=15)),
        "columns": list(public.columns),
        "total_rows": len(public),
        "revision": f"{dataset.id}:{dataset.file_hash}",
    }
    check_json_response(snapshot, "The complete editor snapshot")
    return snapshot


@router.get("/dataset/preview")
@router.get("/dataset-preview")
def get_dataset_preview(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Returns paginated raw data rows from the active dataset.
    """
    _ensure_dataset_loaded(tenant_id, db)
    return TenantDatasetStore.get_preview(tenant_id, limit=limit, offset=offset)


@router.get("/dataset/download")
def download_active_dataset(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Downloads the active tenant dataset as a CSV file with authentication.
    """
    df = _ensure_dataset_loaded(tenant_id, db)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No active dataset uploaded for this company workspace.")

    dataset = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.company_id == tenant_id)
        .order_by(UploadedDataset.created_at.desc())
        .first()
    )
    filename = dataset.filename if dataset else "datalyze_dataset.csv"
    if not filename.lower().endswith(".csv"):
        filename = f"{os.path.splitext(filename)[0]}.csv"

    csv_data = df.to_csv(index=False)
    check_response_size(csv_data, "This CSV download")
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/dataset/query")
def query_dataset(
    payload: Dict[str, Any] = Body(...),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Executes in-memory filtering, grouping, aggregation, or sorting against the active dataset.
    """
    _ensure_dataset_loaded(tenant_id, db)
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
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Returns distinct values and frequencies for a specific column in the active dataset.
    """
    _ensure_dataset_loaded(tenant_id, db)
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

