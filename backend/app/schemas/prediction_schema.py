from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class PredictionOut(BaseModel):
    id: int
    company_id: int
    kpi_id: int
    kpi_name: Optional[str] = None
    forecast_date: datetime
    predicted_value: float
    range_low: float
    range_high: float
    confidence_level: str
    method: str
    model_details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
