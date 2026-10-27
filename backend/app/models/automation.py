"""Durable scheduler state and notification delivery, with database-owned leases."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class SourceRefreshJob(Base):
    __tablename__ = 'source_refresh_jobs'
    # There is one active dataset and therefore at most one automatic writer per company.
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), unique=True, nullable=False)
    source_id = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)
    interval_seconds = Column(Integer, nullable=False, default=3600)
    expected_revision = Column(String(100), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    lease_token = Column(String(64), nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default='scheduled')
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(300), nullable=True)
    last_source_hash = Column(String(64), nullable=True)
    failures = Column(Integer, nullable=False, default=0)


class NotificationOutbox(Base):
    __tablename__ = 'notification_outbox'
    __table_args__ = (UniqueConstraint('company_id', 'event_key', 'destination_id', name='uq_notification_event_destination'),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    event_key = Column(String(100), nullable=False)
    destination_id = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default='pending')
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    lease_token = Column(String(64), nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(300), nullable=True)
