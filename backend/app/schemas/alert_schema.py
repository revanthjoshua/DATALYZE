from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    id: int
    company_id: int
    kpi_id: Optional[int] = None
    detection_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
