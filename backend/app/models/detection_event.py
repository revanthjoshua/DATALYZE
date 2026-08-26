from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_id = Column(Integer, ForeignKey("kpi_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    direction = Column(String(20), nullable=False)  # "up", "down", "anomaly"
    magnitude = Column(Float, nullable=False)  # Absolute change
    percentage_change = Column(Float, nullable=False)  # % change vs baseline
    baseline_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    severity = Column(String(20), default="medium")  # "low", "medium", "high", "critical"
    status = Column(String(20), default="active")  # "active", "acknowledged", "resolved"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    kpi = relationship("KPIDefinition")
    root_causes = relationship("RootCauseResult", back_populates="detection", cascade="all, delete-orphan")

    @property
    def kpi_name(self) -> Optional[str]:
        return self.kpi.name if self.kpi else None
