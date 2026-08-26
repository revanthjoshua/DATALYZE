from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_id = Column(Integer, ForeignKey("kpi_definitions.id", ondelete="SET NULL"), nullable=True)
    detection_id = Column(Integer, ForeignKey("detection_events.id", ondelete="SET NULL"), nullable=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="warning")  # "info", "warning", "critical"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    kpi = relationship("KPIDefinition")
    detection = relationship("DetectionEvent")
    recommendation = relationship("Recommendation")
