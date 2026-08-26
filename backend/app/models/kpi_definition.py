from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class KPIDefinition(Base):
    __tablename__ = "kpi_definitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)  # e.g., "revenue", "orders", "mrr", "churn_rate"
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(100), default="General")  # e.g., Financial, Operational, Sales
    unit = Column(String(50), default="currency")  # currency, percentage, number, count, days
    direction = Column(String(50), default="increase_is_good")  # increase_is_good, decrease_is_good
    calculation_cadence = Column(String(50), default="daily")  # daily, weekly, monthly
    is_active = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="kpis")
    values = relationship("KPIValue", back_populates="kpi", cascade="all, delete-orphan")
