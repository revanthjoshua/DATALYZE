"""Opt-in background source refresh, readiness checks, and durable notifications."""
import logging
import os
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from sqlalchemy import func, select
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.analysis_record import AnalysisRecord
from app.models.company import Company

logger = logging.getLogger('datalyze.monitor')


def scheduler_configuration():
    """Configuration is not evidence that an external scheduler has run."""
    daily = settings.DATALYZE_SCHEDULER_MODE == 'vercel_daily'
    interval = int(os.environ.get('DATALYZE_MONITOR_INTERVAL_SECONDS', '0'))
    configured = bool(settings.CRON_SECRET and len(settings.CRON_SECRET) >= 32) if daily else bool(interval)
    return {'mode': 'vercel_daily' if daily else ('worker' if interval else 'manual'),
            'configured': configured, 'minimum_interval_seconds': 86400 if daily else 300,
            'interval_seconds': 86400 if daily else interval,
            'description': ('Daily checks are configured; the hosting service can run them at any time within the scheduled hour. Missed runs are not retried automatically. Backlogged work continues on later runs.'
                if configured else 'Daily checks are unavailable until the administrator configures the scheduler secret.') if daily else
                (f'Background checks are configured every {interval} seconds.' if interval else
                 'Unattended checks are disabled. Opening or refreshing Monitor checks the current data.')}


def _record_attempt(db, tenant, status):
    # Caller holds the Company lock, so concurrent invocations update one row.
    row = db.query(AnalysisRecord).filter_by(company_id=tenant, kind='monitor_attempt').order_by(AnalysisRecord.id.desc()).first()
    now = datetime.now(timezone.utc)
    content = {'checked_at': now.isoformat(), 'status': status}
    if row:
        row.content = content
        row.created_at = now
    else:
        db.add(AnalysisRecord(company_id=tenant, user_id=None, kind='monitor_attempt',
                              title='Scheduled check attempt', content=content, created_at=now))


def run_cycle(session_factory=SessionLocal, *, deadline=None, max_sources=None,
              max_tenants=None, max_notifications=100, clock=None):
    """Stop starting work after a cooperative deadline; each transaction stays atomic.

    The hosting platform supplies the hard timeout. Python/dataframe work already
    running cannot safely be cancelled, and committed leases recover after expiry.
    """
    from app.api.v1.analysis_routes import monitor
    from app.services.automation_service import refresh_sources, enqueue, deliver_notifications
    clock = clock or time.monotonic
    should_continue = lambda: deadline is None or clock() < deadline
    if not should_continue():
        return 0
    refresh_sources(session_factory, max_items=max_sources, should_continue=should_continue)
    if not should_continue():
        return 0
    with session_factory() as db:
        # One attempt marker per company provides fair retries even after failure.
        # monitor_check.created_at alone cannot do this: unchanged checks reuse it.
        attempts = select(AnalysisRecord.company_id.label('company_id'),
                          func.max(AnalysisRecord.created_at).label('last_attempt')).where(
                              AnalysisRecord.kind == 'monitor_attempt').group_by(AnalysisRecord.company_id).subquery()
        query = select(AnalysisRecord.company_id).outerjoin(attempts,
            attempts.c.company_id == AnalysisRecord.company_id).where(AnalysisRecord.kind == 'monitor').group_by(
                AnalysisRecord.company_id, attempts.c.last_attempt).order_by(
                    attempts.c.last_attempt.asc().nullsfirst(), AnalysisRecord.company_id)
        if max_tenants is not None:
            query = query.limit(max(0, max_tenants))
        tenants = list(db.scalars(query))
    checked = 0
    for tenant in tenants:
        if not should_continue():
            break
        with session_factory() as db:
            try:
                company = db.query(Company).filter_by(id=tenant).with_for_update(skip_locked=True).first()
                if company is None:
                    continue
                result = monitor(SimpleNamespace(company_id=tenant), db)
                latest = db.query(AnalysisRecord).filter_by(company_id=tenant, kind='monitor_check').order_by(AnalysisRecord.id.desc()).first()
                signature = [(c['name'], c['alert'], c['threshold']) for c in result['checks']]
                prior = [(c['name'], c['alert'], c['threshold']) for c in latest.content['checks']] if latest else None
                content = {k: v for k, v in result.items() if k not in ['mode', 'background']}
                if latest and prior == signature and latest.dataset_revision == result['revision']:
                    latest.content = content
                else:
                    event = AnalysisRecord(company_id=tenant, user_id=None, kind='monitor_check',
                        title='Scheduled data readiness check', dataset_revision=result['revision'], content=content)
                    db.add(event)
                    db.flush()
                    was_alerting = bool(latest and any(c['alert'] for c in latest.content['checks']))
                    is_alerting = any(c['alert'] for c in content['checks'])
                    if (is_alerting or was_alerting) and prior != signature:
                        try:
                            enqueue(db, tenant, f'monitor:{event.id}', {'event': 'monitor_alert' if is_alerting else 'monitor_recovered',
                                'revision': result['revision'], 'checked_at': content['checked_at'], 'checks': content['checks']})
                        except ValueError:
                            logger.warning('Notification configuration invalid for company %s', tenant)
                _record_attempt(db, tenant, 'completed')
                db.commit()
                checked += 1
            except Exception:
                db.rollback()
                # A failure must not keep this tenant at the front of every batch.
                try:
                    if db.query(Company).filter_by(id=tenant).with_for_update(skip_locked=True).first() is not None:
                        _record_attempt(db, tenant, 'failed')
                        db.commit()
                except Exception:
                    db.rollback()
                logger.warning('Scheduled data check failed for company %s', tenant)
    if should_continue():
        deliver_notifications(session_factory, max_items=max_notifications, should_continue=should_continue)
    return checked


if __name__ == '__main__':
    print(f'Companies checked: {run_cycle()}')
