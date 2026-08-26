import io
import csv
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.report import Report
from app.repositories.report_repository import ReportRepository
from app.repositories.kpi_repository import KPIRepository


class ReportingService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.report_repo = ReportRepository(db, tenant_id=tenant_id)
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)

    def generate_kpi_summary_csv(self, user_id: Optional[int] = None) -> str:
        """Generates CSV content of all active KPIs and their latest values"""
        active_kpis = self.kpi_repo.get_active_kpis()
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["KPI Key", "KPI Name", "Category", "Unit", "Direction", "Latest Value", "Last Recorded Date"])
        
        for kpi in active_kpis:
            latest = self.kpi_repo.get_latest_kpi_value(kpi.id)
            val_str = f"{latest.value:.2f}" if latest else "N/A"
            date_str = latest.timestamp.strftime("%Y-%m-%d") if latest else "N/A"
            writer.writerow([kpi.key, kpi.name, kpi.category, kpi.unit, kpi.direction, val_str, date_str])

        # Record Report in DB
        report_record = Report(
            company_id=self.tenant_id,
            user_id=user_id,
            title="KPI Summary Export",
            report_type="kpi_summary",
            status="generated"
        )
        self.db.add(report_record)
        self.db.commit()

        return output.getvalue()

    def generate_kpi_trend_csv(self, kpi_id: int, user_id: Optional[int] = None) -> str:
        kpi = self.kpi_repo.get_by_id(kpi_id)
        history = self.kpi_repo.get_kpi_values(kpi_id, limit=365)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", f"{kpi.name} ({kpi.unit})", "Source File"])
        
        for h in history:
            writer.writerow([h.timestamp.strftime("%Y-%m-%d"), f"{h.value:.2f}", h.source_file or "Direct Ingestion"])

        return output.getvalue()
