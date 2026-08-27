"""
Comprehensive Multi-Tenant Dataset Isolation & Deletion Persistence Verification Test
-------------------------------------------------------------------------------------
Verifies:
1. Fresh Company A and Company B start with clean empty states (no automatic sample data).
2. Company A uploads Dataset A -> Only Company A sees Dataset A and generated KPIs/anomalies/predictions.
3. Company B registers/logs in -> Sees 0 datasets, 0 KPIs, 0 alerts (Strict tenant isolation).
4. Company B uploads Dataset B -> Sees only Dataset B and SaaS KPIs.
5. Company A logs back in -> Sees only Dataset A and Retail KPIs.
6. Company A deletes Dataset A -> Only Company A's dataset, KPIs, values, alerts, predictions are deleted.
7. Company B's Dataset B and SaaS analytics remain 100% intact in database and memory.
8. Re-login / refresh verification for Company A confirms clean empty state persists.
"""
import os
import sys
import uuid
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set cwd to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app.core.database import Base
from app.models.company import Company
from app.models.user import User
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.models.detection_event import DetectionEvent
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.alert import Alert
from app.models.report import Report
from app.models.inventory_item import InventoryItem
from app.models.warehouse_location import WarehouseLocation
from app.models.uploaded_dataset import UploadedDataset
from app.services.auth_service import AuthService
from app.services.data_processing_service import DataProcessingService
from app.services.inventory_service import InventoryService
from app.services.kpi_service import KPIService
from app.services.dataset_store import TenantDatasetStore
from app.schemas.user_schema import AdminRegistrationRequest


def run_multi_tenant_isolation_tests():
    test_db_file = f"test_isolation_{uuid.uuid4().hex[:8]}.db"
    test_db_url = f"sqlite:///./{test_db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Initialize tables
    Base.metadata.create_all(bind=engine)
    TenantDatasetStore.clear_all()

    print("=" * 80)
    print("  DATALYZE: MULTI-TENANT DATASET ISOLATION & DELETE PERSISTENCE TEST")
    print("=" * 80)

    db = TestingSessionLocal()
    try:
        auth_service = AuthService(db)

        # -------------------------------------------------------------
        # 1. Register Company A (Apex Retail) & Company B (CloudFlow SaaS)
        # -------------------------------------------------------------
        print("\n[STEP 1] Registering Company A and Company B...")
        reg_a = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Alice Admin",
                username="alice_apex",
                phone_number="+15550111",
                email="alice@apexretail.com",
                password="SecurePassword123!",
                confirm_password="SecurePassword123!",
                company_name="Apex Retail Corp",
                industry="Retail/E-commerce"
            )
        )
        company_a_id = reg_a["company"]["id"]
        user_a_id = reg_a["user"].id
        print(f"  -> Created Company A: ID={company_a_id}, Name='{reg_a['company']['name']}'")

        reg_b = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Bob Admin",
                username="bob_cloudflow",
                phone_number="+15550222",
                email="bob@cloudflow.io",
                password="SecurePassword123!",
                confirm_password="SecurePassword123!",
                company_name="CloudFlow Technologies",
                industry="SaaS/Technology"
            )
        )
        company_b_id = reg_b["company"]["id"]
        user_b_id = reg_b["user"].id
        print(f"  -> Created Company B: ID={company_b_id}, Name='{reg_b['company']['name']}'")

        assert company_a_id != company_b_id, "Company IDs must be distinct"

        # -------------------------------------------------------------
        # 2. Verify Initial Clean Empty State for Both Companies
        # -------------------------------------------------------------
        print("\n[STEP 2] Verifying initial clean empty state (No auto-seeded demo data)...")
        inv_service_a = InventoryService(db, tenant_id=company_a_id)
        summary_a = inv_service_a.get_inventory_summary()
        assert summary_a.total_items == 0, f"Expected 0 items for fresh Company A, got {summary_a.total_items}"
        assert summary_a.total_warehouses == 0, f"Expected 0 warehouses for fresh Company A, got {summary_a.total_warehouses}"

        inv_service_b = InventoryService(db, tenant_id=company_b_id)
        summary_b = inv_service_b.get_inventory_summary()
        assert summary_b.total_items == 0, f"Expected 0 items for fresh Company B, got {summary_b.total_items}"

        kpi_service_a = KPIService(db, tenant_id=company_a_id)
        assert len(kpi_service_a.list_kpis()) == 0, "Expected 0 KPIs for fresh Company A"

        kpi_service_b = KPIService(db, tenant_id=company_b_id)
        assert len(kpi_service_b.list_kpis()) == 0, "Expected 0 KPIs for fresh Company B"
        print("  [PASS] Both companies start with 0 items, 0 warehouses, and 0 KPIs.")

        # -------------------------------------------------------------
        # 3. Company A Uploads Dataset A (Retail Dataset)
        # -------------------------------------------------------------
        print("\n[STEP 3] Company A uploading Dataset A (Retail Sales: 100 rows)...")
        df_a = pd.DataFrame({
            "order_date": pd.date_range("2026-07-01", periods=100, freq="D").strftime("%Y-%m-%d"),
            "order_id": [f"ORD-APX-{1000+i}" for i in range(100)],
            "revenue": [150.0 + (i * 2.5) for i in range(100)],
            "units_sold": [2 + (i % 5) for i in range(100)],
            "region": ["North", "South", "East", "West"] * 25,
            "sku": [f"SKU-APX-{100 + (i % 4)}" for i in range(100)],
            "product_name": [f"Apex Item {i % 4}" for i in range(100)],
            "stock_level": [50 - (i % 15) for i in range(100)],
            "reorder_point": [20] * 100,
            "warehouse": ["Apex Central Hub"] * 100
        })

        proc_a = DataProcessingService(db, tenant_id=company_a_id)
        resp_a = proc_a.process_dataframe(df_a, source_filename="apex_retail_sales.csv")
        assert resp_a.status == "success", "Company A upload should succeed"
        assert resp_a.processed_rows == 100, "Should process 100 rows"

        # Check persistent dataset record created for Company A
        dataset_record_a = db.query(UploadedDataset).filter(UploadedDataset.company_id == company_a_id).first()
        assert dataset_record_a is not None, "UploadedDataset record must exist in DB for Company A"
        assert dataset_record_a.filename == "apex_retail_sales.csv"
        assert dataset_record_a.row_count == 100
        assert dataset_record_a.file_hash is not None
        print(f"  [PASS] Company A dataset recorded in DB (hash: {dataset_record_a.file_hash[:12]}..., rows: {dataset_record_a.row_count})")

        # Verify Company A has KPIs and inventory
        kpis_a = kpi_service_a.list_kpis()
        assert len(kpis_a) > 0, "Company A must have generated KPIs"
        kpi_keys_a = [k.key for k in kpis_a]
        assert "revenue" in kpi_keys_a, "Company A must have 'revenue' KPI"
        print(f"  [PASS] Company A generated {len(kpis_a)} KPIs: {kpi_keys_a}")

        # -------------------------------------------------------------
        # 4. Strict Isolation Check: Company B MUST NOT see Company A's data
        # -------------------------------------------------------------
        print("\n[STEP 4] Verifying Company B sees NO data from Company A (Strict Isolation)...")
        # 1. Dataset metadata in memory
        meta_b = TenantDatasetStore.get_metadata(company_b_id)
        assert meta_b is None, "Company B in-memory dataset store must be None"

        # 2. Dataset records in DB
        db_datasets_b = db.query(UploadedDataset).filter(UploadedDataset.company_id == company_b_id).all()
        assert len(db_datasets_b) == 0, f"Expected 0 DB dataset records for Company B, got {len(db_datasets_b)}"

        # 3. KPIs in DB
        kpis_b = kpi_service_b.list_kpis()
        assert len(kpis_b) == 0, f"Expected 0 KPIs for Company B, got {len(kpis_b)}"

        # 4. KPI values in DB
        kpi_vals_b = db.query(KPIValue).filter(KPIValue.company_id == company_b_id).all()
        assert len(kpi_vals_b) == 0, f"Expected 0 KPI values for Company B, got {len(kpi_vals_b)}"

        # 5. Detections in DB
        detections_b = db.query(DetectionEvent).filter(DetectionEvent.company_id == company_b_id).all()
        assert len(detections_b) == 0, f"Expected 0 Detections for Company B, got {len(detections_b)}"

        # 6. Inventory in DB
        summary_b_check = inv_service_b.get_inventory_summary()
        assert summary_b_check.total_items == 0, f"Company B must have 0 inventory items, got {summary_b_check.total_items}"
        print("  [PASS] Company B is 100% isolated: 0 datasets, 0 KPIs, 0 detections, 0 inventory items.")

        # -------------------------------------------------------------
        # 5. Company B Uploads Dataset B (SaaS Metrics: 60 rows)
        # -------------------------------------------------------------
        print("\n[STEP 5] Company B uploading Dataset B (SaaS Metrics: 60 rows)...")
        df_b = pd.DataFrame({
            "date": pd.date_range("2026-07-01", periods=60, freq="D").strftime("%Y-%m-%d"),
            "mrr": [40000.0 + (i * 120.0) for i in range(60)],
            "churn_rate": [1.5 + (i * 0.02) for i in range(60)],
            "active_users": [1200 + (i * 15) for i in range(60)],
            "plan_tier": ["Enterprise", "Pro", "Starter"] * 20
        })

        proc_b = DataProcessingService(db, tenant_id=company_b_id)
        resp_b = proc_b.process_dataframe(df_b, source_filename="cloudflow_saas_metrics.csv")
        assert resp_b.status == "success", "Company B upload should succeed"
        assert resp_b.processed_rows == 60, "Should process 60 rows"

        dataset_record_b = db.query(UploadedDataset).filter(UploadedDataset.company_id == company_b_id).first()
        assert dataset_record_b is not None, "UploadedDataset record must exist in DB for Company B"
        assert dataset_record_b.filename == "cloudflow_saas_metrics.csv"
        assert dataset_record_b.row_count == 60

        kpis_b_after = kpi_service_b.list_kpis()
        kpi_keys_b = [k.key for k in kpis_b_after]
        assert "mrr" in kpi_keys_b, "Company B must have 'mrr' KPI"
        assert "churn_rate" in kpi_keys_b, "Company B must have 'churn_rate' KPI"
        assert "revenue" not in kpi_keys_b, "Company B must NOT have Company A's 'revenue' KPI"
        print(f"  [PASS] Company B recorded its dataset and generated SaaS KPIs: {kpi_keys_b}")

        # -------------------------------------------------------------
        # 6. Verify Company A Still Sees ONLY Dataset A
        # -------------------------------------------------------------
        print("\n[STEP 6] Verifying Company A state is untouched by Company B's upload...")
        meta_a = TenantDatasetStore.get_metadata(company_a_id)
        assert meta_a is not None, "Company A metadata must still exist in memory"
        assert meta_a["filename"] == "apex_retail_sales.csv", f"Expected apex_retail_sales.csv, got {meta_a['filename']}"
        assert meta_a["row_count"] == 100, f"Expected 100 rows, got {meta_a['row_count']}"

        kpis_a_after = kpi_service_a.list_kpis()
        kpi_keys_a_after = [k.key for k in kpis_a_after]
        assert "revenue" in kpi_keys_a_after, "Company A must still have 'revenue' KPI"
        assert "mrr" not in kpi_keys_a_after, "Company A must NOT have Company B's 'mrr' KPI"
        print("  [PASS] Company A retains Dataset A with 100 rows and Retail KPIs only.")

        # -------------------------------------------------------------
        # 7. Company A Deletes Dataset A (Cascading Deletion)
        # -------------------------------------------------------------
        print("\n[STEP 7] Company A deletes Dataset A (Testing Cascading Deletion)...")
        delete_result_a = proc_a.delete_active_dataset()
        assert delete_result_a["success"] is True, "Delete active dataset should return success"
        print(f"  -> Deleted summary for Company A: {delete_result_a['deleted_summary']}")

        # Verify Company A has 0 records across all tables
        assert TenantDatasetStore.get_metadata(company_a_id) is None, "Company A in-memory store must be cleared"
        assert db.query(UploadedDataset).filter(UploadedDataset.company_id == company_a_id).count() == 0, "UploadedDataset for A must be 0"
        assert db.query(KPIDefinition).filter(KPIDefinition.company_id == company_a_id).count() == 0, "KPIDefinition for A must be 0"
        assert db.query(KPIValue).filter(KPIValue.company_id == company_a_id).count() == 0, "KPIValue for A must be 0"
        assert db.query(DetectionEvent).filter(DetectionEvent.company_id == company_a_id).count() == 0, "DetectionEvent for A must be 0"
        assert db.query(Prediction).filter(Prediction.company_id == company_a_id).count() == 0, "Prediction for A must be 0"
        assert db.query(Recommendation).filter(Recommendation.company_id == company_a_id).count() == 0, "Recommendation for A must be 0"
        assert db.query(Alert).filter(Alert.company_id == company_a_id).count() == 0, "Alert for A must be 0"
        assert db.query(Report).filter(Report.company_id == company_a_id).count() == 0, "Report for A must be 0"
        assert db.query(InventoryItem).filter(InventoryItem.company_id == company_a_id).count() == 0, "InventoryItem for A must be 0"
        assert db.query(WarehouseLocation).filter(WarehouseLocation.company_id == company_a_id).count() == 0, "WarehouseLocation for A must be 0"
        print("  [PASS] Company A's dataset and ALL downstream intelligence records completely deleted.")

        # -------------------------------------------------------------
        # 8. Verify Company B's Data Remains Completely Intact
        # -------------------------------------------------------------
        print("\n[STEP 8] Verifying Company B's Dataset B and SaaS KPIs remain 100% intact...")
        meta_b_after = TenantDatasetStore.get_metadata(company_b_id)
        assert meta_b_after is not None, "Company B in-memory metadata must still exist"
        assert meta_b_after["filename"] == "cloudflow_saas_metrics.csv", f"Expected cloudflow_saas_metrics.csv, got {meta_b_after['filename']}"
        assert meta_b_after["row_count"] == 60, f"Expected 60 rows, got {meta_b_after['row_count']}"

        assert db.query(UploadedDataset).filter(UploadedDataset.company_id == company_b_id).count() == 1, "Company B must still have 1 UploadedDataset"
        assert db.query(KPIDefinition).filter(KPIDefinition.company_id == company_b_id).count() > 0, "Company B must still have KPIDefinition records"
        assert db.query(KPIValue).filter(KPIValue.company_id == company_b_id).count() > 0, "Company B must still have KPIValue records"
        assert db.query(Prediction).filter(Prediction.company_id == company_b_id).count() > 0, "Company B must still have Prediction records"
        print("  [PASS] Company B's Dataset B and analytics remain 100% intact.")

        # -------------------------------------------------------------
        # 9. Re-Login / Persistence Verification for Company A
        # -------------------------------------------------------------
        print("\n[STEP 9] Re-authenticating Company A to verify clean empty state persistence...")
        from app.schemas.user_schema import UserLogin
        login_a = auth_service.authenticate_user(
            UserLogin(
                email=reg_a["user"].email,
                password="SecurePassword123!",
                portal_type="admin"
            )
        )
        assert login_a["company"]["id"] == company_a_id, "Authenticated user must match Company A ID"


        # Query services again as Company A after re-login
        kpi_summaries_a = kpi_service_a.get_dashboard_kpi_summaries()
        assert len(kpi_summaries_a) == 0, "Re-authenticated Company A must see 0 KPI summaries"

        inv_summary_a_relogin = inv_service_a.get_inventory_summary()
        assert inv_summary_a_relogin.total_items == 0, "Re-authenticated Company A must see 0 inventory items"
        print("  [PASS] Re-login verification confirms permanent clean empty state for Company A.")

        print("\n" + "=" * 80)
        print("  ALL 9 MULTI-TENANT ISOLATION & DELETE PERSISTENCE TESTS PASSED! 100% VERIFIED")
        print("=" * 80)

    finally:
        db.close()
        # Clean up test database file and memory store
        TenantDatasetStore.clear_all()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass


if __name__ == "__main__":
    run_multi_tenant_isolation_tests()
