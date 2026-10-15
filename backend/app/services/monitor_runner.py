"""Opt-in background source refresh, readiness checks, and durable notifications."""
import logging
from types import SimpleNamespace
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.analysis_record import AnalysisRecord
from app.models.company import Company

logger=logging.getLogger('datalyze.monitor')


def run_cycle(session_factory=SessionLocal):
    from app.api.v1.analysis_routes import monitor
    from app.services.automation_service import refresh_sources, enqueue, deliver_notifications
    refresh_sources(session_factory)
    with session_factory() as db:
        tenants=list(db.scalars(select(AnalysisRecord.company_id).where(AnalysisRecord.kind=='monitor').distinct()))
    checked=0
    for tenant in tenants:
        with session_factory() as db:
            try:
                # Serialize a company's state transition and outbox event across workers.
                db.query(Company).filter_by(id=tenant).with_for_update().first()
                result=monitor(SimpleNamespace(company_id=tenant),db)
                latest=db.query(AnalysisRecord).filter_by(company_id=tenant,kind='monitor_check').order_by(AnalysisRecord.id.desc()).first()
                signature=[(c['name'],c['alert'],c['threshold']) for c in result['checks']]
                prior=[(c['name'],c['alert'],c['threshold']) for c in latest.content['checks']] if latest else None
                content={k:v for k,v in result.items() if k not in ['mode','background']}
                if latest and prior==signature and latest.dataset_revision==result['revision']:
                    latest.content=content
                else:
                    event = AnalysisRecord(company_id=tenant,user_id=None,kind='monitor_check',title='Scheduled data readiness check',dataset_revision=result['revision'],content=content)
                    db.add(event)
                    db.flush()
                    was_alerting = bool(latest and any(c['alert'] for c in latest.content['checks']))
                    is_alerting = any(c['alert'] for c in content['checks'])
                    if (is_alerting or was_alerting) and prior != signature:
                        try:
                            enqueue(db, tenant, f'monitor:{event.id}', {'event':'monitor_alert' if is_alerting else 'monitor_recovered',
                                'revision':result['revision'], 'checked_at':content['checked_at'], 'checks':content['checks']})
                        except ValueError:
                            logger.warning('Notification configuration invalid for company %s',tenant)
                db.commit()
                checked+=1
            except Exception:
                db.rollback()
                logger.warning('Scheduled data check failed for company %s',tenant)
    deliver_notifications(session_factory)
    return checked


if __name__=='__main__':
    print(f'Companies checked: {run_cycle()}')
