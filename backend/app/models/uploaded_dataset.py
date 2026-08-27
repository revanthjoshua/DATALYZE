from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    row_count = Column(Integer, default=0, nullable=False)
    col_count = Column(Integer, default=0, nullable=False)
    schema_metadata = Column(JSON, nullable=True)
    detected_profile = Column(JSON, nullable=True)
    storage_path = Column(String(500), nullable=True)
    source_type = Column(String(50), default="upload", nullable=False)  # upload, sample, stream, edit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    company = relationship("Company", backref="uploaded_datasets")
