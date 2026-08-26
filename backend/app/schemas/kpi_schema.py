from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class KPIDefinitionBase(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    category: str = "General"
    unit: str = "currency"
    direction: str = "increase_is_good"
    calculation_cadence: str = "daily"
    is_active: bool = True
    is_custom: bool = False


class KPIDefinitionCreate(KPIDefinitionBase):
    pass


class KPIDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    direction: Optional[str] = None
    calculation_cadence: Optional[str] = None
    is_active: Optional[bool] = None


class KPIDefinitionOut(KPIDefinitionBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KPIValueBase(BaseModel):
    kpi_id: int
    timestamp: datetime
    value: float
    dimension_data: Optional[Dict[str, Any]] = None
    source_file: Optional[str] = None


class KPIValueCreate(KPIValueBase):
    pass


class KPIValueOut(KPIValueBase):
    id: int
    company_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KPISummaryCard(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    category: str
    unit: str
    direction: str
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    percentage_change: Optional[float] = None
    trend_direction: Optional[str] = None  # "up", "down", "neutral"
    status: str = "healthy"  # "healthy", "warning", "critical"
    recent_history: List[KPIValueOut] = []
