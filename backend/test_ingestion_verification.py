import io
import pandas as pd
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_processing_service import DataProcessingService
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.kpi_definition import KPIDefinition

def test_all():
    print("Testing Universal Data Ingestion & Processing...")
    
    # 1. Test Ingestion Service with CSV
    csv_bytes = b"date,order_id,revenue,units,region,channel\n2026-08-01,ORD-1,$150.00,2,North,Online\n2026-08-02,ORD-2,$220.50,3,South,POS\n"
    svc = DataIngestionService(tenant_id=1)
    df_csv = svc.parse_raw_content(csv_bytes, "test.csv")
    assert len(df_csv) == 2, f"Expected 2 rows, got {len(df_csv)}"
    print("CSV ingestion test passed!")

    # 2. Test Ingestion Service with Excel .xlsx
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_csv.to_excel(writer, index=False, sheet_name='SalesData')
    xlsx_bytes = buffer.getvalue()
    
    df_xlsx = svc.parse_raw_content(xlsx_bytes, "test.xlsx")
    assert len(df_xlsx) == 2, f"Expected 2 rows from xlsx, got {len(df_xlsx)}"
    print("Excel .xlsx ingestion test passed!")

    # 3. Test Ingestion Service with Custom Dynamic Columns
    custom_csv = b"date,transaction_id,defect_rate,energy_kwh,operator,factory_line\n2026-08-01,TX-1,1.5%,450 kWh,John,Line-A\n2026-08-02,TX-2,2.1%,490 kWh,Jane,Line-B\n"
    df_custom = svc.parse_raw_content(custom_csv, "iot_manufacturing.csv")
    
    db = SessionLocal()
    try:
        # Check tenant 1 exists
        company = db.query(Company).filter(Company.id == 1).first()
        if not company:
            company = Company(id=1, name="Demo Test Co", industry="Manufacturing", currency="USD")
            db.add(company)
            db.commit()
            
        proc_svc = DataProcessingService(db, tenant_id=1)
        res = proc_svc.process_dataframe(df_custom, "iot_manufacturing.csv")
        assert res.status in ["success", "partial_success"], f"Expected success, got {res.status}"
        assert res.processed_rows == 2, f"Expected 2 processed rows, got {res.processed_rows}"
        print(f"Data Processing pipeline passed! Message: {res.message}")
        print("Updated KPIs:", res.kpis_updated)
    finally:
        db.close()

if __name__ == "__main__":
    test_all()
