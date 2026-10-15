"""Real source replacement and durable scheduling; all outbound delivery is mocked."""
import json
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.company import Company
from app.models.analysis_record import AnalysisRecord
from app.models.automation import SourceRefreshJob, NotificationOutbox
from app.services.data_processing_service import DataProcessingService
from app.services.dataset_store import TenantDatasetStore
from app.services import automation_service as automation
from app.api.v1.analysis_routes import active, revision


@pytest.fixture
def factory(monkeypatch):
    monkeypatch.setattr(TenantDatasetStore, '_store', {})
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON', '[]')
    monkeypatch.setenv('DATALYZE_SOURCES_JSON', json.dumps([
        {'id':'sales','name':'Sales','type':'api','url':'https://example.test/sales','company_ids':[1,2],'allow_refresh':True}]))
    engine = create_engine('sqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        db.add_all([Company(id=1,name='First'),Company(id=2,name='Second')])
        db.commit()
    yield factory
    engine.dispose()


def frame(value):
    return pd.DataFrame({'date':['2026-10-01','2026-10-02'],'region':['North','South'],'revenue':[value,value+1]})


def seed(factory, tenant):
    with factory() as db:
        DataProcessingService(db,tenant).process_dataframe(frame(10),'original.csv')
        current = revision(active(db,tenant))
        automation.configure_schedule(db,tenant,'sales',True,300,current)
        return current


def test_refresh_is_tenant_scoped_unchanged_is_idempotent_and_manual_edit_pauses(factory,monkeypatch):
    original = seed(factory,1)
    monkeypatch.setattr(automation,'fetch_source',lambda _:frame(30))
    now = datetime.now(timezone.utc)+timedelta(seconds=1)
    assert automation.refresh_sources(factory,now)==1
    with factory() as db:
        job=db.query(SourceRefreshJob).one()
        assert job.status=='refreshed' and job.expected_revision!=original
        assert job.expected_revision==revision(active(db,1))
        assert active(db,2) is None
        backups=db.query(AnalysisRecord).filter_by(company_id=1,kind='backup').count()
        refreshed_revision=job.expected_revision
    assert automation.refresh_sources(factory,now+timedelta(seconds=301))==1
    with factory() as db:
        assert db.query(SourceRefreshJob).one().status=='unchanged'
        assert revision(active(db,1))==refreshed_revision
        assert db.query(AnalysisRecord).filter_by(company_id=1,kind='backup').count()==backups
        DataProcessingService(db,1).process_dataframe(frame(99),'manual.csv')
        manual_revision=revision(active(db,1))
    assert automation.refresh_sources(factory,now+timedelta(seconds=602))==0
    with factory() as db:
        job=db.query(SourceRefreshJob).one()
        assert job.status=='paused' and job.enabled is False
        assert revision(active(db,1))==manual_revision


def test_failed_connection_does_not_block_another_tenant(factory,monkeypatch):
    seed(factory,1); seed(factory,2)
    calls=[]
    def fetch(_):
        calls.append(True)
        if len(calls)==1:
            raise RuntimeError('private-password-must-not-leak')
        return frame(50)
    monkeypatch.setattr(automation,'fetch_source',fetch)
    assert automation.refresh_sources(factory,datetime.now(timezone.utc)+timedelta(seconds=1))==1
    with factory() as db:
        first=db.query(SourceRefreshJob).filter_by(company_id=1).one()
        second=db.query(SourceRefreshJob).filter_by(company_id=2).one()
        assert first.status=='failed' and first.enabled
        assert 'private-password' not in first.last_error
        assert second.status=='refreshed'


def test_checkpoint_failure_rolls_back_dataset_and_backup(factory):
    old=seed(factory,1)
    def fail(_):
        raise RuntimeError('checkpoint interrupted')
    with factory() as db:
        before=db.query(AnalysisRecord).filter_by(kind='backup').count()
        with pytest.raises(RuntimeError):
            DataProcessingService(db,1).process_dataframe(frame(80),'replacement.csv',expected_revision=old,on_success=fail)
        assert revision(active(db,1))==old
        assert db.query(AnalysisRecord).filter_by(kind='backup').count()==before


def test_notification_dedup_retries_stable_key_and_acceptance(factory,monkeypatch):
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON',json.dumps([{'id':'ops','type':'webhook','company_ids':[1],'enabled':True,'url':'https://example.test/notify'}]))
    with factory() as db:
        automation.enqueue(db,1,'event-1',{'event':'monitor_alert'})
        automation.enqueue(db,1,'event-1',{'event':'monitor_alert'})
        automation.enqueue(db,2,'event-1',{'event':'monitor_alert'})
        db.commit()
        assert db.query(NotificationOutbox).count()==1
    calls=[]
    def flaky(destination,payload,key):
        calls.append(key)
        if len(calls)==1:
            raise RuntimeError('private-provider-response')
    now=datetime.now(timezone.utc)+timedelta(seconds=1)
    assert automation.deliver_notifications(factory,now,sender=flaky)==0
    with factory() as db:
        row=db.query(NotificationOutbox).one()
        assert row.status=='retrying' and row.attempts==1
        assert 'private-provider' not in row.last_error
    assert automation.deliver_notifications(factory,now+timedelta(minutes=3),sender=flaky)==1
    assert calls[0]==calls[1]
    assert automation.deliver_notifications(factory,now+timedelta(hours=1),sender=flaky)==0
    with factory() as db:
        row=db.query(NotificationOutbox).one()
        assert row.status=='accepted' and row.attempts==2 and row.accepted_at is not None


def test_removed_destination_blocks_delivery_and_failed_delivery_stops_after_five(factory,monkeypatch):
    config=[{'id':'ops','type':'email','company_ids':[1],'enabled':True,'recipients':['nobody@example.test']}]
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON',json.dumps(config))
    with factory() as db:
        automation.enqueue(db,1,'removed',{'event':'monitor_alert'})
        db.commit()
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON','[]')
    calls=[]
    assert automation.deliver_notifications(factory,sender=lambda *args:calls.append(args))==0
    assert calls==[]
    with factory() as db:
        assert db.query(NotificationOutbox).one().status=='blocked'
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON',json.dumps(config))
    with factory() as db:
        automation.enqueue(db,1,'failing',{'event':'monitor_alert'});db.commit()
    def fail(*args):
        calls.append(args)
        raise RuntimeError('provider down')
    now=datetime.now(timezone.utc)
    for hour in range(6):
        automation.deliver_notifications(factory,now+timedelta(hours=hour+1),sender=fail)
    assert len(calls)==5
    with factory() as db:
        assert db.query(NotificationOutbox).filter_by(event_key='failing').one().status=='failed'


def test_database_lease_has_only_one_winner_across_sessions(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'leases.sqlite'),connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    now=datetime.now(timezone.utc)
    with factory() as db:
        db.add(Company(id=1,name='Lease tenant'));db.commit()
        row=SourceRefreshJob(company_id=1,source_id='sales',enabled=True,next_run_at=now)
        db.add(row);db.commit();row_id=row.id
    def compete(_):
        with factory() as db:
            return automation.claim(db,SourceRefreshJob,row_id,now,SourceRefreshJob.enabled.is_(True))
    with ThreadPoolExecutor(max_workers=2) as executor:
        tokens=list(executor.map(compete,range(2)))
    assert sum(t is not None for t in tokens)==1
    engine.dispose()


def test_schedule_api_permissions_and_status_redaction(client,db_session,monkeypatch):
    from app.models.user import User
    response=client.post('/api/v1/auth/register-admin',json={'full_name':'Schedule Owner','phone_number':'+1555111222',
        'email':'schedule-owner@example.com','username':'scheduleowner','password':'Password123!','confirm_password':'Password123!',
        'company_name':'Scheduled','industry':'Retail/E-commerce'})
    assert response.status_code==201,response.text
    headers={'Authorization':'Bearer '+response.json()['access_token']}
    user=db_session.query(User).filter_by(username='scheduleowner').one()
    monkeypatch.setenv('DATALYZE_SOURCES_JSON',json.dumps([{'id':'sales','type':'api','url':'https://private.test','headers':{'Authorization':'private-token'},'company_ids':[user.company_id],'allow_refresh':True}]))
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON',json.dumps([{'id':'ops','type':'webhook','url':'https://private-destination.test','headers':{'Authorization':'private-token'},'company_ids':[user.company_id],'enabled':True}]))
    DataProcessingService(db_session,user.company_id).process_dataframe(frame(10),'first.csv')
    current=revision(active(db_session,user.company_id))
    payload={'enabled':True,'interval_seconds':300,'expected_revision':current}
    assert client.put('/api/v1/sources/sales/schedule',headers=headers,json=payload).status_code==200
    state=client.get('/api/v1/sources/automation/status',headers=headers)
    assert state.status_code==200
    assert 'private' not in state.text
    assert state.json()['schedule']['enabled'] is True
    user.role='viewer';db_session.commit()
    assert client.get('/api/v1/sources/automation/status',headers=headers).status_code==200
    assert client.put('/api/v1/sources/sales/schedule',headers=headers,json=payload).status_code==403



@pytest.mark.parametrize('old_sender_fails', [False, True])
def test_stale_notification_worker_cannot_overwrite_successor(factory, monkeypatch, old_sender_fails):
    monkeypatch.setenv('DATALYZE_NOTIFICATIONS_JSON', json.dumps([
        {'id': 'ops', 'type': 'webhook', 'company_ids': [1], 'enabled': True,
         'url': 'https://example.test/notify'}]))
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    with factory() as db:
        automation.enqueue(db, 1, 'stale-owner', {'event': 'monitor_alert'})
        db.commit()

    def delayed_sender(*_):
        # Simulate the lease expiring during provider IO and a successor taking over.
        with factory() as successor:
            row = successor.query(NotificationOutbox).one()
            row.attempts = 2
            if old_sender_fails:
                row.status = 'accepted'
                row.accepted_at = now
                row.last_error = None
                row.lease_token = row.lease_until = None
            else:
                row.status = 'retrying'
                row.lease_token = 'successor-lease'
                row.lease_until = now + timedelta(minutes=10)
                row.last_error = 'Successor is processing the retry.'
            successor.commit()
        if old_sender_fails:
            raise RuntimeError('The old provider request failed after takeover.')

    # The old worker must not count delivery or overwrite the new owner's state.
    assert automation.deliver_notifications(factory, now, sender=delayed_sender) == 0
    with factory() as db:
        row = db.query(NotificationOutbox).one()
        assert row.attempts == 2
        if old_sender_fails:
            assert row.status == 'accepted' and row.accepted_at is not None
            assert row.last_error is None and row.lease_token is None
        else:
            assert row.status == 'retrying' and row.accepted_at is None
            assert row.lease_token == 'successor-lease' and row.lease_until is not None
            assert row.last_error == 'Successor is processing the retry.'
