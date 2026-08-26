from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_id = Column(Integer, ForeignKey("kpi_definitions.id", ondelete="SET NULL"), nullable=True)
    detection_id = Column(Integer, ForeignKey("detection_events.id", ondelete="SET NULL"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    action_text = Column(Text, nullable=False)  # Specific, practical action
    rationale = Column(Text, nullable=True)  # Plain-language explanation of why this was recommended
    impact_level = Column(String(20), default="medium")  # "low", "medium", "high"
    priority = Column(String(20), default="standard")  # "urgent", "standard", "low"
    category = Column(String(50), default="operations")  # "pricing", "inventory", "marketing", "operations"
    status = Column(String(20), default="open")  # "open", "in_progress", "completed", "dismissed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    kpi = relationship("KPIDefinition")
    detection = relationship("DetectionEvent")
    prediction = relationship("Prediction")
