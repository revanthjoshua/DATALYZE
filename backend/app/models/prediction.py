from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_id = Column(Integer, ForeignKey("kpi_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)
    range_low = Column(Float, nullable=False)  # Lower bound of confidence interval
    range_high = Column(Float, nullable=False)  # Upper bound of confidence interval
    confidence_level = Column(String(50), default="moderate")  # "low", "moderate", "high"
    method = Column(String(100), default="trend_seasonal_decomposition")
    model_details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    kpi = relationship("KPIDefinition")
