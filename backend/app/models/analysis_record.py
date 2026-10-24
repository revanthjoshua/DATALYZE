from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.core.database import Base


class AnalysisRecord(Base):
    __tablename__ = 'analysis_records'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    kind = Column(String(32), nullable=False)
    title = Column(String(200), nullable=False)
    dataset_revision = Column(String(100), nullable=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
