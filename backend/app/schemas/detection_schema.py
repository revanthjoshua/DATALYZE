from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RootCauseResultOut(BaseModel):
    id: int
    company_id: int
    detection_id: int
    dimension_name: str
    dimension_value: str
    contribution_percentage: float
    explanation_text: str
    confidence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionEventOut(BaseModel):
    id: int
    company_id: int
    kpi_id: int
    detected_at: datetime
    direction: str
    magnitude: float
    percentage_change: float
    baseline_value: float
    current_value: float
    severity: str
    status: str
    created_at: datetime
    kpi_name: Optional[str] = None
    root_causes: List[RootCauseResultOut] = []

    model_config = ConfigDict(from_attributes=True)
