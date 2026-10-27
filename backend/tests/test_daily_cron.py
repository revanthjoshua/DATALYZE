"""Free-host scheduling is authenticated, bounded and fair; no external calls."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import analysis_routes, internal_cron_routes
from app.core.config import settings
from app.core.database import Base
from app.models.analysis_record import AnalysisRecord
from app.models.automation import SourceRefreshJob, NotificationOutbox
from app.models.company import Company
from app.services import automation_service as automation, monitor_runner
from app.services.data_processing_service import DataProcessingService
from app.services.dataset_store import TenantDatasetStore


@pytest.fixture
def cron_client(monkeypatch):
    monkeypatch.delenv('VERCEL_ENV', raising=False)
    monkeypatch.setattr(settings, 'DATALYZE_SCHEDULER_MODE', 'vercel_daily')
    monkeypatch.setattr(settings, 'CRON_SECRET', 'only-a-test-cron-secret-with-32-or-more-characters')
    app = FastAPI()
    app.include_router(internal_cron_routes.router, prefix='/api/v1')
    return TestClient(app)


@pytest.mark.parametrize('authorization', [None, 'Bearer wrong', 'Basic unrelated', 'Bearer \u00e9\u00e9'])
def test_cron_rejects_bad_authorization_without_starting_work(cron_client, monkeypatch, authorization):
    def forbidden(**_):
        pytest.fail('An unauthorized request started scheduled work.')
    monkeypatch.setattr(internal_cron_routes, 'run_cycle', forbidden)
    headers = {'Authorization': authorization} if authorization else {}
    # ASGI headers are Latin-1 bytes; this also exercises non-ASCII comparison.
    response = cron_client.get('/api/v1/internal/cron', headers={k:v.encode('utf-8') for k,v in headers.items()})
    assert response.status_code == 401
    assert settings.CRON_SECRET not in response.text


@pytest.mark.parametrize('mode,secret', [('manual', 'x'*40), ('vercel_daily', None), ('vercel_daily', 'short')])
def test_cron_fails_closed_when_not_configured(cron_client, monkeypatch, mode, secret):
    monkeypatch.setattr(settings, 'DATALYZE_SCHEDULER_MODE', mode)
    monkeypatch.setattr(settings, 'CRON_SECRET', secret)
    monkeypatch.setattr(internal_cron_routes, 'run_cycle', lambda **_: pytest.fail('Unconfigured work started.'))
    response = cron_client.get('/api/v1/internal/cron', headers={'Authorization':'Bearer '+str(secret)})
    assert response.status_code == 503


def test_authorized_cron_waits_for_bounded_cycle_and_disables_caching(cron_client, monkeypatch):
    observed = []
    monkeypatch.setattr(internal_cron_routes.time, 'monotonic', lambda: 100.0)
    def cycle(**limits):
        observed.append(limits)
        return 3
    monkeypatch.setattr(internal_cron_routes, 'run_cycle', cycle)
    response = cron_client.get('/api/v1/internal/cron', headers={'Authorization':'Bearer '+settings.CRON_SECRET})
    assert response.status_code == 200
    assert observed == [{'deadline':340.0, 'max_sources':2, 'max_tenants':10, 'max_notifications':5}]
    assert response.json()['checked_companies'] == 3
    assert response.json()['budget_exhausted'] is False
    assert response.headers['cache-control'] == 'no-store'
    assert settings.CRON_SECRET not in response.text


@pytest.fixture
def scheduled(monkeypatch):
    monkeypatch.delenv('VERCEL_ENV', raising=False)
    monkeypatch.setattr(settings, 'DATALYZE_SCHEDULER_MODE', 'manual')
    monkeypatch.setattr(settings, 'CRON_SECRET', None)
    monkeypatch.setattr(TenantDatasetStore, '_store', {})
    monkeypatch.setenv('DATALYZE_MONITOR_INTERVAL_SECONDS', '0')
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON', '[]')
    monkeypatch.setenv('DATALYZE_SOURCES_JSON', json.dumps([{
        'id':'sales', 'name':'Sales', 'type':'api', 'url':'https://example.test/sales',
        'company_ids':[1,2,3,4], 'allow_refresh':True}]))
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        db.add_all([Company(id=i, name=f'Daily company {i}') for i in range(1,5)])
        db.commit()
    yield factory
    engine.dispose()


def source_data(factory, tenant, schedule=False):
    with factory() as db:
        frame = pd.DataFrame({'date':['2026-10-01','2026-10-02'], 'region':['North','South'], 'revenue':[10,20]})
        DataProcessingService(db, tenant).process_dataframe(frame, 'daily.csv')
        current = analysis_routes.revision(analysis_routes.active(db, tenant))
        if schedule:
            automation.configure_schedule(db, tenant, 'sales', True, 300, current)
        return current


def monitor_rule(factory, tenant):
    with factory() as db:
        db.add(AnalysisRecord(company_id=tenant, kind='monitor', title='Rule',
            content={'max_age_hours':24, 'max_missing_percent':10}))
        db.commit()


def test_daily_schedule_enforces_minimum_and_reports_actual_mode(scheduled, monkeypatch):
    current = source_data(scheduled, 1)
    monkeypatch.setattr(settings, 'DATALYZE_SCHEDULER_MODE', 'vercel_daily')
    monkeypatch.setattr(settings, 'CRON_SECRET', 'configured-test-only-secret-at-least-32-characters')
    with scheduled() as db:
        with pytest.raises(HTTPException) as error:
            automation.configure_schedule(db, 1, 'sales', True, 3600, current)
        assert error.value.status_code == 422
        assert db.query(SourceRefreshJob).count() == 0
        result = automation.configure_schedule(db, 1, 'sales', True, 86400, current)
        assert result['interval_seconds'] == 86400
        # Disabling an old hourly schedule remains possible after a host migration.
        assert automation.configure_schedule(db, 1, 'sales', False, 3600, current)['enabled'] is False
    status = monitor_runner.scheduler_configuration()
    assert status['mode'] == 'vercel_daily' and status['configured'] is True
    assert status['minimum_interval_seconds'] == status['interval_seconds'] == 86400
    assert 'Daily' in status['description'] and 'not retried automatically' in status['description']
    monkeypatch.setattr(settings, 'CRON_SECRET', None)
    assert monitor_runner.scheduler_configuration()['configured'] is False


def test_expired_budget_starts_no_database_or_outbound_work():
    def no_database():
        pytest.fail('An expired cycle touched the database.')
    assert monitor_runner.run_cycle(no_database, deadline=10, clock=lambda:10) == 0


def test_expiring_during_sources_does_not_start_monitor_queries(monkeypatch):
    monkeypatch.setattr(automation, 'refresh_sources', lambda *args,**kwargs:0)
    ticks = iter([0,11])
    def no_database():
        pytest.fail('A new phase started after the budget expired.')
    assert monitor_runner.run_cycle(no_database, deadline=10, clock=lambda:next(ticks)) == 0


def test_monitor_batches_advance_past_failed_tenants(scheduled):
    for tenant in range(1,5):
        monitor_rule(scheduled, tenant)
    # The first two tenants have no dataset. They must not permanently starve 3/4.
    source_data(scheduled, 3)
    source_data(scheduled, 4)
    assert monitor_runner.run_cycle(scheduled, max_sources=0, max_tenants=2, max_notifications=0) == 0
    assert monitor_runner.run_cycle(scheduled, max_sources=0, max_tenants=2, max_notifications=0) == 2
    with scheduled() as db:
        attempts = {r.company_id:r.content['status'] for r in db.query(AnalysisRecord).filter_by(kind='monitor_attempt')}
        assert attempts == {1:'failed', 2:'failed', 3:'completed', 4:'completed'}
        assert db.query(AnalysisRecord).filter_by(kind='monitor_attempt').count() == 4


def test_unchanged_monitor_checks_still_rotate_fairly(scheduled, monkeypatch):
    class Clock(datetime):
        current = datetime(2026,10,19,tzinfo=timezone.utc)
        @classmethod
        def now(cls, tz=None):
            return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)
    monkeypatch.setattr(monitor_runner, 'datetime', Clock)
    for tenant in (1,2,3):
        source_data(scheduled, tenant)
        monitor_rule(scheduled, tenant)
    for _ in range(6):
        assert monitor_runner.run_cycle(scheduled, max_sources=0, max_tenants=1, max_notifications=0) == 1
        Clock.current += timedelta(minutes=1)
    with scheduled() as db:
        attempts = {r.company_id:r.created_at.replace(tzinfo=timezone.utc) for r in db.query(AnalysisRecord).filter_by(kind='monitor_attempt')}
        assert attempts == {i:datetime(2026,10,19,0,i+2,tzinfo=timezone.utc) for i in (1,2,3)}
        # Unchanged checks update their existing record; attempt markers stay bounded.
        assert db.query(AnalysisRecord).filter_by(kind='monitor_check').count() == 3
        assert db.query(AnalysisRecord).filter_by(kind='monitor_attempt').count() == 3


def test_monitor_deadline_stops_before_next_tenant(scheduled, monkeypatch):
    for tenant in (1,2):
        source_data(scheduled, tenant)
        monitor_rule(scheduled, tenant)
    ticks = iter([0,0,0,11,11])
    # Entry, after sources, before each tenant, then before notification delivery.
    assert monitor_runner.run_cycle(scheduled, deadline=10, clock=lambda:next(ticks),
        max_sources=0, max_tenants=2, max_notifications=0) == 1
    with scheduled() as db:
        assert [r.company_id for r in db.query(AnalysisRecord).filter_by(kind='monitor_attempt')] == [1]


def test_source_batch_skips_active_leases_and_works_oldest_due_first(scheduled, monkeypatch):
    for tenant in (1,2,3):
        source_data(scheduled, tenant, schedule=True)
    now = datetime.now(timezone.utc)+timedelta(seconds=1)
    with scheduled() as db:
        jobs = {r.company_id:r for r in db.query(SourceRefreshJob)}
        for tenant, job in jobs.items():
            job.next_run_at = now-timedelta(minutes=tenant)
        jobs[3].lease_token = 'other-worker'
        jobs[3].lease_until = now+timedelta(minutes=5)
        db.commit()
    calls = []
    def fetched(_):
        calls.append(True)
        return pd.DataFrame({'date':['2026-10-01','2026-10-02'], 'region':['North','South'], 'revenue':[30,40]})
    monkeypatch.setattr(automation, 'fetch_source', fetched)
    assert automation.refresh_sources(scheduled, now, max_items=2, should_continue=lambda:False) == 0
    assert calls == []
    assert automation.refresh_sources(scheduled, now, max_items=1) == 1
    with scheduled() as db:
        assert db.query(SourceRefreshJob).filter_by(company_id=2).one().status == 'refreshed'
        assert db.query(SourceRefreshJob).filter_by(company_id=1).one().status == 'scheduled'
        assert db.query(SourceRefreshJob).filter_by(company_id=3).one().lease_token == 'other-worker'
    assert automation.refresh_sources(scheduled, now, max_items=1) == 1
    assert len(calls) == 2


def test_notification_batch_skips_active_leases_and_obeys_budget(scheduled, monkeypatch):
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON', json.dumps([{
        'id':'ops', 'type':'webhook', 'url':'https://example.test/notify', 'company_ids':[1], 'enabled':True}]))
    now = datetime.now(timezone.utc)+timedelta(seconds=1)
    with scheduled() as db:
        for index in range(3):
            automation.enqueue(db, 1, str(index), {'event':f'event-{index}'})
        db.commit()
        rows = db.query(NotificationOutbox).order_by(NotificationOutbox.id).all()
        for index, row in enumerate(rows):
            row.next_attempt_at = now-timedelta(minutes=index+1)
        rows[2].lease_token = 'active-other-worker'
        rows[2].lease_until = now+timedelta(minutes=5)
        db.commit()
    sent = []
    sender = lambda destination,payload,key:sent.append(payload['event'])
    assert automation.deliver_notifications(scheduled, now, sender=sender, max_items=1) == 1
    assert sent == ['event-1']
    assert automation.deliver_notifications(scheduled, now, sender=sender, max_items=1, should_continue=lambda:False) == 0
    assert sent == ['event-1']
    assert automation.deliver_notifications(scheduled, now, sender=sender, max_items=1) == 1
    assert sent == ['event-1','event-0']
    with scheduled() as db:
        held = db.query(NotificationOutbox).filter_by(event_key='2').one()
        assert held.lease_token == 'active-other-worker' and held.attempts == 0


def test_internal_attempt_markers_are_not_public_analysis_evidence(scheduled):
    monitor_rule(scheduled, 1)
    monitor_runner.run_cycle(scheduled, max_sources=0, max_tenants=1, max_notifications=0)
    user = SimpleNamespace(company_id=1)
    with scheduled() as db:
        marker = db.query(AnalysisRecord).filter_by(kind='monitor_attempt').one()
        assert all(row['kind'] != 'monitor_attempt' for row in analysis_routes.list_records(user, db))
        with pytest.raises(HTTPException) as error:
            analysis_routes.download(marker.id, user, db)
        assert error.value.status_code == 404


def test_preview_does_not_advertise_or_allow_unattended_refresh(scheduled, monkeypatch):
    current = source_data(scheduled, 1)
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    monkeypatch.setattr(settings, 'DATALYZE_SCHEDULER_MODE', 'vercel_daily')
    monkeypatch.setattr(settings, 'CRON_SECRET', 'configured-test-only-secret-at-least-32-characters')

    status = monitor_runner.scheduler_configuration()
    assert status['mode'] == 'vercel_daily'
    assert status['configured'] is False
    assert 'Preview' in status['description'] and 'Production' in status['description']

    with scheduled() as db:
        with pytest.raises(HTTPException) as error:
            automation.configure_schedule(db, 1, 'sales', True, 86400, current)
        assert error.value.status_code == 422
        assert 'Preview' in str(error.value.detail)
        assert db.query(SourceRefreshJob).count() == 0


def test_preview_cron_never_starts_scheduled_work(cron_client, monkeypatch):
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    monkeypatch.setattr(internal_cron_routes, 'run_cycle',
        lambda **_: pytest.fail('Preview must never start scheduled work.'))
    response = cron_client.get('/api/v1/internal/cron',
        headers={'Authorization': 'Bearer ' + settings.CRON_SECRET})
    assert response.status_code == 503
    assert 'Preview' in response.json()['detail']
    assert settings.CRON_SECRET not in response.text
