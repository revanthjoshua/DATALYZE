from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DatasetStorageBlob(Base):
    """
    Persistent serverless-compatible dataset storage stored directly in PostgreSQL/SQLite.
    Guarantees 100% free, zero-config, tenant-isolated dataset persistence across
    serverless cold starts on Vercel and Neon PostgreSQL.
    """
    __tablename__ = "dataset_storage_blobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False, index=True)
    compressed_data = Column(LargeBinary, nullable=False)
    content_type = Column(String(100), default="text/csv", nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    company = relationship("Company", backref="dataset_storage_blobs")
