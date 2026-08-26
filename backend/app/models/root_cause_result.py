from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class RootCauseResult(Base):
    __tablename__ = "root_cause_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    detection_id = Column(Integer, ForeignKey("detection_events.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension_name = Column(String(100), nullable=False)  # e.g., "region", "product_category", "channel"
    dimension_value = Column(String(255), nullable=False)  # e.g., "Region East", "Electronics"
    contribution_percentage = Column(Float, nullable=False)  # e.g., 68.4
    explanation_text = Column(Text, nullable=False)  # e.g., "68% of the revenue drop came from Region East"
    confidence_score = Column(Float, default=0.85)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    detection = relationship("DetectionEvent", back_populates="root_causes")
