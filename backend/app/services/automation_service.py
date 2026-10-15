"""Opt-in refresh and durable notification delivery; never stores connection secrets."""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.models.automation import SourceRefreshJob, NotificationOutbox
from app.services.source_connector_service import configured_sources, fetch_source

logger = logging.getLogger('datalyze.automation')
LEASE_SECONDS = 600
MAX_ATTEMPTS = 5


def utcnow():
    return datetime.now(timezone.utc)


def destinations(tenant):
    try:
        items = json.loads(os.environ.get('DATALYZE_NOTIFICATIONS_JSON', '[]'))
        if not isinstance(items, list):
            raise ValueError()
        result = []
        seen = set()
        for item in items:
            if not isinstance(item, dict) or item.get('enabled') is not True or tenant not in item.get('company_ids', []):
                continue
            key = item.get('id')
            if not isinstance(key, str) or not key or len(key) > 100 or key in seen or item.get('type') not in ['webhook', 'email']:
                raise ValueError()
            seen.add(key)
            result.append(item)
        return result
    except (ValueError, TypeError):
        raise ValueError('Notification configuration needs administrator attention.') from None


def enqueue(db, tenant, event_key, payload):
    """Outbox rows commit with the event; unique keys prevent duplicate enqueue."""
    for destination in destinations(tenant):
        if db.query(NotificationOutbox.id).filter_by(company_id=tenant, event_key=event_key, destination_id=destination['id']).first():
            continue
        try:
            with db.begin_nested():
                db.add(NotificationOutbox(company_id=tenant, event_key=event_key,
                    destination_id=destination['id'], payload=payload))
                db.flush()
        except IntegrityError:
            # A concurrent worker already queued the same event/destination.
            pass


def claim(db, model, row_id, now, eligibility):
    token = uuid.uuid4().hex
    changed = db.execute(update(model).where(model.id == row_id, eligibility,
        or_(model.lease_until.is_(None), model.lease_until <= now)).values(
        lease_token=token, lease_until=now + timedelta(seconds=LEASE_SECONDS)))
    db.commit()
    return token if changed.rowcount == 1 else None


def schedule_view(row):
    if row is None:
        return None
    return {key: getattr(row, key) for key in ['source_id', 'enabled', 'interval_seconds',
        'expected_revision', 'next_run_at', 'status', 'last_run_at', 'last_error', 'failures']}


def configure_schedule(db, tenant, source_id, enabled, interval, expected_revision):
    from app.api.v1.analysis_routes import active, revision
    config = next((s for s in configured_sources(tenant) if s.get('id') == source_id), None)
    if config is None:
        raise HTTPException(404, 'Source not configured for this company.')
    if enabled and config.get('allow_refresh') is not True:
        raise HTTPException(422, 'An administrator must explicitly allow automatic refresh for this connection.')
    # Serialize schedule edits with worker claims before inspecting the lease.
    # populate_existing also refreshes a row already present in this session.
    row = db.query(SourceRefreshJob).filter_by(company_id=tenant).populate_existing().with_for_update().first()
    if row and row.lease_until and row.lease_until.replace(tzinfo=timezone.utc) > utcnow():
        raise HTTPException(409, 'A refresh is running. Try again once it completes.')
    current = revision(active(db, tenant))
    if enabled and (not current or current != expected_revision):
        raise HTTPException(409, 'Import and review the source first, then enable refresh against its current revision.')
    if row is None:
        row = SourceRefreshJob(company_id=tenant)
        db.add(row)
    row.source_id = source_id
    row.enabled = enabled
    row.interval_seconds = interval
    row.expected_revision = current
    row.next_run_at = utcnow()
    row.status = 'scheduled' if enabled else 'disabled'
    row.last_error = None
    row.last_source_hash = None
    row.failures = 0
    row.lease_until = row.lease_token = None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'The schedule changed concurrently. Refresh and try again.') from None
    return schedule_view(row)


def refresh_sources(session_factory, now=None):
    from app.api.v1.analysis_routes import active, revision
    from app.services.data_processing_service import DataProcessingService
    now = now or utcnow()
    with session_factory() as db:
        ids = [r[0] for r in db.query(SourceRefreshJob.id).filter(SourceRefreshJob.enabled.is_(True), SourceRefreshJob.next_run_at <= now).all()]
    refreshed = 0
    for row_id in ids:
        with session_factory() as db:
            token = claim(db, SourceRefreshJob, row_id, now, SourceRefreshJob.enabled.is_(True) & (SourceRefreshJob.next_run_at <= now))
            if not token:
                continue
            row = db.get(SourceRefreshJob, row_id)
            try:
                config = next((s for s in configured_sources(row.company_id) if s.get('id') == row.source_id), None)
                if config is None or config.get('allow_refresh') is not True:
                    raise HTTPException(409, 'Automatic refresh is no longer allowed by the connection configuration.')
                if revision(active(db, row.company_id)) != row.expected_revision:
                    raise HTTPException(409, 'Active data changed outside this schedule. Review it and explicitly resume refresh.')
                frame = fetch_source(config)
                source_hash = hashlib.sha256(frame.to_csv(index=False).encode('utf-8')).hexdigest()
                # Recheck ownership after network IO: an expired worker may not write.
                db.refresh(row)
                if row.lease_token != token or not row.enabled:
                    continue
                # Hold a write lock until the dataset and checkpoint commit together.
                owned = db.execute(update(SourceRefreshJob).where(SourceRefreshJob.id == row.id,
                    SourceRefreshJob.lease_token == token, SourceRefreshJob.enabled.is_(True)).values(
                    lease_until=utcnow() + timedelta(seconds=LEASE_SECONDS)))
                if owned.rowcount != 1:
                    db.rollback()
                    continue
                if revision(active(db, row.company_id)) != row.expected_revision:
                    raise HTTPException(409, 'Active data changed during refresh. Review it and explicitly resume refresh.')

                def checkpoint(_result=None):
                    row.expected_revision = revision(active(db, row.company_id))
                    row.last_source_hash = source_hash
                    row.status = 'unchanged' if unchanged else 'refreshed'
                    row.last_run_at = now
                    row.next_run_at = now + timedelta(seconds=row.interval_seconds)
                    row.last_error = None
                    row.failures = 0
                    row.lease_until = row.lease_token = None

                unchanged = row.last_source_hash == source_hash
                if unchanged:
                    checkpoint()
                    db.commit()
                else:
                    DataProcessingService(db, row.company_id).process_dataframe(frame, f'connected_{row.source_id}.csv',
                        expected_revision=row.expected_revision, on_success=checkpoint)
                refreshed += 1
            except Exception as error:
                db.rollback()
                row = db.get(SourceRefreshJob, row_id)
                if row is None or row.lease_token != token:
                    continue
                conflict = isinstance(error, HTTPException) and error.status_code == 409
                row.enabled = not conflict
                row.status = 'paused' if conflict else 'failed'
                row.failures += 1
                row.last_run_at = now
                row.next_run_at = now + timedelta(seconds=min(86400, row.interval_seconds * 2 ** min(row.failures, 6)))
                row.last_error = str(error.detail)[:300] if conflict else 'Source refresh failed. Check connection availability, read permissions and supported limits.'
                row.lease_until = row.lease_token = None
                # One failure notification per failure incident, not every retry.
                if row.failures == 1:
                    try:
                        enqueue(db, row.company_id, f'refresh:{row.id}:{now.isoformat()}',
                            {'event': 'source_refresh_failed', 'source_id': row.source_id, 'status': row.status, 'message': row.last_error})
                    except ValueError:
                        logger.warning('Notification configuration invalid for company %s', row.company_id)
                db.commit()
                logger.warning('Source refresh failed for company %s (%s)', row.company_id, type(error).__name__)
    return refreshed


def send_notification(destination, payload, idempotency_key):
    """Returns only after provider acceptance; acceptance is not inbox delivery."""
    headers = {'Idempotency-Key': idempotency_key}
    if destination['type'] == 'webhook':
        url = destination.get('url', '')
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Webhook requires an operator-approved HTTPS endpoint.')
        headers.update(destination.get('headers', {}))
        headers['Idempotency-Key'] = idempotency_key
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(url, json={'id': idempotency_key, **payload}, headers=headers)
            if not 200 <= response.status_code < 300:
                raise ValueError('Webhook did not accept notification.')
    else:
        recipients = destination.get('recipients', [])
        if not settings.RESEND_API_KEY or not isinstance(recipients, list) or not 1 <= len(recipients) <= 20 or any(not isinstance(r, str) or '@' not in r or '\n' in r or '\r' in r for r in recipients):
            raise ValueError('Email notification configuration is incomplete.')
        headers['Authorization'] = f'Bearer {settings.RESEND_API_KEY}'
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post('https://api.resend.com/emails', headers=headers, json={
                'from': settings.RESEND_FROM_EMAIL, 'to': recipients,
                'subject': 'DATALYZE monitoring update', 'text': json.dumps(payload, indent=2, ensure_ascii=False)})
            response.raise_for_status()
            if not response.json().get('id'):
                raise ValueError('Email provider did not return an acceptance ID.')


def deliver_notifications(session_factory, now=None, sender=None):
    now = now or utcnow()
    sender = sender or send_notification
    with session_factory() as db:
        ids = [r[0] for r in db.query(NotificationOutbox.id).filter(NotificationOutbox.status.in_(['pending', 'retrying']),
            NotificationOutbox.next_attempt_at <= now).order_by(NotificationOutbox.id).limit(100).all()]
    accepted = 0
    for row_id in ids:
        with session_factory() as db:
            token = claim(db, NotificationOutbox, row_id, now, NotificationOutbox.status.in_(['pending', 'retrying']) & (NotificationOutbox.next_attempt_at <= now))
            if not token:
                continue
            row = db.get(NotificationOutbox, row_id)
            company_id, destination_id, payload, attempts = row.company_id, row.destination_id, row.payload, row.attempts
            # Never dirty an ORM row whose lease can change during external IO.
            db.expunge(row)
            final = {'lease_until': None, 'lease_token': None}
            try:
                destination = next((d for d in destinations(company_id) if d['id'] == destination_id), None)
                if destination is None:
                    final.update(status='blocked', last_error='The destination was removed or disabled; nothing was sent.')
                else:
                    # Commit the attempt only while this worker still owns the lease.
                    attempt = db.execute(update(NotificationOutbox).where(
                        NotificationOutbox.id == row_id, NotificationOutbox.lease_token == token
                    ).values(attempts=NotificationOutbox.attempts + 1).execution_options(synchronize_session=False))
                    if attempt.rowcount != 1:
                        db.rollback()
                        continue
                    db.commit()
                    attempts += 1
                    sender(destination, payload, f'datalyze-{company_id}-{row_id}')
                    final.update(status='accepted', accepted_at=now, last_error=None)
            except Exception:
                db.rollback()
                final.update(status='failed' if attempts >= MAX_ATTEMPTS else 'retrying',
                    next_attempt_at=now + timedelta(seconds=min(3600, 60 * 2 ** min(attempts, 6))),
                    last_error='Destination did not confirm acceptance. Check notification configuration and provider status.')
            # A worker that outlives its lease cannot overwrite a successor's result.
            completed = db.execute(update(NotificationOutbox).where(
                NotificationOutbox.id == row_id, NotificationOutbox.lease_token == token
            ).values(**final).execution_options(synchronize_session=False))
            db.commit()
            if completed.rowcount == 1 and final['status'] == 'accepted':
                accepted += 1
    return accepted
