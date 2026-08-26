from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    title: str
    report_type: str  # "kpi_summary", "trend_report", "detection_report"
    parameters: Optional[Dict[str, Any]] = None


class ReportOut(BaseModel):
    id: int
    company_id: int
    user_id: Optional[int] = None
    title: str
    report_type: str
    parameters: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
