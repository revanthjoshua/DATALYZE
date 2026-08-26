from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecommendationOut(BaseModel):
    id: int
    company_id: int
    kpi_id: Optional[int] = None
    kpi_name: Optional[str] = None
    detection_id: Optional[int] = None
    prediction_id: Optional[int] = None
    title: str
    action_text: str
    rationale: Optional[str] = None
    impact_level: str
    priority: str
    category: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
