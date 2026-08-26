from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NoahQueryRequest(BaseModel):
    question: str
    kpi_id: Optional[int] = None
    time_frame: Optional[str] = "30d"  # "7d", "30d", "90d", "all"
    context: Optional[Dict[str, Any]] = None


class NoahDataReference(BaseModel):
    source_type: str  # "kpi", "detection", "prediction", "recommendation", "inventory"
    title: str
    value: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class NoahQueryResponse(BaseModel):
    question: str
    answer: str
    structured_data: Optional[Dict[str, Any]] = None
    references: List[NoahDataReference] = []
    suggested_actions: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NoahAgenticStep(BaseModel):
    step_index: int
    title: str
    stage: str  # "understand" | "inspect" | "slice" | "forecast" | "prescribe"
    tool_called: str
    status: str = "completed"
    duration_ms: int = 120
    summary: str
    details: Optional[Dict[str, Any]] = None


class NoahAgenticPlanRequest(BaseModel):
    goal: str
    kpi_id: Optional[int] = None


class NoahAgenticPlanResponse(BaseModel):
    goal: str
    company_name: str
    execution_time_ms: int
    steps: List[NoahAgenticStep]
    executive_insight: str
    synthesized_recommendation: str
    confidence_score: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
