"""Private operator endpoint for a bounded, once-daily Vercel invocation."""
import os
import secrets
import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.monitor_runner import run_cycle

router = APIRouter(prefix='/internal', tags=['Operations'])


@router.get('/cron', include_in_schema=False)
def daily_cron(request: Request):
    secret = settings.CRON_SECRET
    if settings.DATALYZE_SCHEDULER_MODE != 'vercel_daily' or not secret or len(secret) < 32:
        raise HTTPException(503, 'Scheduled execution is not configured.')
    supplied = request.headers.get('authorization', '')
    if not secrets.compare_digest(supplied.encode('utf-8'), f'Bearer {secret}'.encode('utf-8')):
        raise HTTPException(401, 'Scheduler authorization required.')
    if os.environ.get('VERCEL_ENV', '').strip().lower() == 'preview':
        raise HTTPException(503, 'Scheduled execution is unavailable on Vercel Preview deployments.')
    deadline = time.monotonic() + 240
    checked = run_cycle(deadline=deadline, max_sources=2, max_tenants=10, max_notifications=5)
    return JSONResponse({'checked_companies': checked, 'bounded_run': True,
        'budget_exhausted': time.monotonic() >= deadline,
        'limits': {'sources': 2, 'companies': 10, 'notifications': 5}},
        headers={'Cache-Control': 'no-store'})
