"""Scheduled checks exercise real persisted datasets in an isolated database."""
from datetime import datetime, timedelta, timezone
import hashlib

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.analysis_record import AnalysisRecord
from app.models.company import Company
from app.models.uploaded_dataset import UploadedDataset
from app.services.dataset_store import TenantDatasetStore
from app.services.monitor_runner import run_cycle
from app.services.storage_service import DatabaseStorageBackend


@pytest.fixture
def monitoring(monkeypatch):
    from app.api.v1 import analysis_routes

    class Clock(datetime):
        current = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)

    # Restore the previous cache automatically: no test sees another test's data.
    monkeypatch.setattr(TenantDatasetStore, '_store', {})
    monkeypatch.setattr(analysis_routes, 'datetime', Clock)
    monkeypatch.setenv('DATALYZE_MONITOR_INTERVAL_SECONDS', '60')
    engine = create_engine('sqlite:///:memory:',
                           connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    try:
        yield factory, Clock
    finally:
        engine.dispose()


def seed(factory, clock, tenant, csv=None, missing_limit=10):
    with factory() as db:
        db.add(Company(id=tenant, name=f'Monitor tenant {tenant}'))
        db.add(AnalysisRecord(company_id=tenant, kind='monitor', title='Readiness rule',
                              content={'max_age_hours': 24, 'max_missing_percent': missing_limit}))
        db.commit()
        if csv is not None:
            blob = csv.encode()
            key = DatabaseStorageBackend().save(tenant, 'source.csv', blob, db=db)
            db.add(UploadedDataset(company_id=tenant, filename='source.csv', storage_path=key,
                                   file_hash=hashlib.sha256(blob).hexdigest(), row_count=2,
                                   col_count=2, created_at=clock.current - timedelta(hours=1)))
            db.commit()


def checks(factory, tenant):
    with factory() as db:
        return db.query(AnalysisRecord).filter_by(company_id=tenant, kind='monitor_check').order_by(AnalysisRecord.id).all()


def test_cycle_uses_each_tenants_persisted_source_and_records_checks(monitoring):
    factory, clock = monitoring
    seed(factory, clock, 1, 'key,value\nA,10\nB,20\n')
    seed(factory, clock, 2, 'key,value\nX,\nY,30\n')
    # Deliberately stale, incorrect cached data must not determine readiness.
    TenantDatasetStore.set_dataset(1, pd.DataFrame({'stale': [None]}))
    TenantDatasetStore.set_dataset(2, pd.DataFrame({'stale': [100]}))

    assert run_cycle(factory) == 2
    first, second = checks(factory, 1), checks(factory, 2)
    assert len(first) == len(second) == 1
    assert first[0].content['checks'][1]['value'] == 0
    assert first[0].content['checks'][1]['alert'] is False
    assert second[0].content['checks'][1]['value'] == 25
    assert second[0].content['checks'][1]['alert'] is True
    assert first[0].dataset_revision != second[0].dataset_revision
    assert first[0].user_id is None
    assert first[0].content['checked_at'] == clock.current.isoformat()
    assert TenantDatasetStore.get_dataset(1)['key'].tolist() == ['A', 'B']
    assert TenantDatasetStore.get_dataset(2)['key'].tolist() == ['X', 'Y']


def test_unchanged_status_refreshes_check_and_threshold_or_revision_creates_transition(monitoring):
    factory, clock = monitoring
    seed(factory, clock, 1, 'key,value\nA,10\nB,20\n')
    assert run_cycle(factory) == 1
    original = checks(factory, 1)[0]
    clock.current += timedelta(minutes=5)
    assert run_cycle(factory) == 1
    rows = checks(factory, 1)
    assert len(rows) == 1
    assert rows[0].id == original.id
    assert rows[0].content['checked_at'] == clock.current.isoformat()
    assert rows[0].content['checked_at'] != original.content['checked_at']

    # Even when both thresholds pass, changing the rule deserves a new record.
    with factory() as db:
        db.add(AnalysisRecord(company_id=1, kind='monitor', title='Revised rule',
                              content={'max_age_hours': 48, 'max_missing_percent': 5}))
        db.commit()
    assert run_cycle(factory) == 1
    assert len(checks(factory, 1)) == 2

    with factory() as db:
        dataset = db.query(UploadedDataset).filter_by(company_id=1).one()
        dataset.file_hash = 'new-source-revision'
        db.commit()
    assert run_cycle(factory) == 1
    rows = checks(factory, 1)
    assert len(rows) == 3
    assert rows[-1].dataset_revision.endswith(':new-source-revision')

    clock.current += timedelta(hours=49)
    assert run_cycle(factory) == 1
    rows = checks(factory, 1)
    assert len(rows) == 4
    assert rows[-1].content['checks'][0]['alert'] is True
    assert rows[-2].content['checks'][0]['alert'] is False


def test_missing_dataset_does_not_prevent_other_tenants_checks(monitoring, caplog):
    factory, clock = monitoring
    seed(factory, clock, 1)
    seed(factory, clock, 2, 'key,value\nA,10\nB,20\n')
    assert run_cycle(factory) == 1
    assert checks(factory, 1) == []
    assert len(checks(factory, 2)) == 1
    assert 'Scheduled data check failed for company 1' in caplog.text
