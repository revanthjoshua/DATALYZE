import io
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user, require_analyst_user, require_admin_user
from app.models.user import User
from app.models.analysis_record import AnalysisRecord
from app.api.v1.analysis_routes import active, revision, insert, source, backup
from app.services.source_connector_service import configured_sources, fetch_source
from app.services.analyst_service import records
from app.services.data_processing_service import DataProcessingService

router = APIRouter(prefix='/sources', tags=['Data connections'])


@router.get('')
def list_sources(user: User = Depends(get_current_user)):
    try:
        return [{'id':s['id'], 'name':s.get('name',s['id']), 'type':s['type'], 'allow_refresh':s.get('allow_refresh') is True} for s in configured_sources(user.company_id)]
    except (ValueError, KeyError):
        raise HTTPException(503, 'Source configuration needs administrator attention.')


@router.post('/{source_id}/preview')
def preview(source_id:str,user:User=Depends(require_analyst_user),db:Session=Depends(get_db)):
    try:
        config = next((s for s in configured_sources(user.company_id) if s.get('id')==source_id),None)
        if not config: raise HTTPException(404,'Source not configured for this company.')
        frame=fetch_source(config)
    except ValueError as error:
        raise HTTPException(422,str(error))
    rev=revision(active(db,user.company_id))
    row=insert(db,user,'import_preview',f"Source preview: {config.get('name',source_id)}"[:200],
               {'csv':frame.to_csv(index=False),'source_id':source_id,'rows':len(frame)},rev)
    return {'preview_id':row.id,'rows':len(frame),'columns':list(frame.columns),'preview':records(frame.head(30)), 'revision':rev}


class ImportInput(BaseModel):
    preview_id:int


class ScheduleInput(BaseModel):
    enabled: bool
    interval_seconds: int = Field(default=3600, ge=300, le=86400)
    expected_revision: str | None = Field(default=None, max_length=100)


@router.get('/automation/status')
def automation_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.monitor_runner import scheduler_configuration
    from app.models.automation import SourceRefreshJob, NotificationOutbox
    from app.services.automation_service import schedule_view, destinations
    try:
        channels = [{'id':d['id'], 'name':d.get('name',d['id']), 'type':d['type']} for d in destinations(user.company_id)]
        configuration_error = None
    except ValueError as error:
        channels, configuration_error = [], str(error)
    execution = scheduler_configuration()
    recent = db.query(NotificationOutbox).filter_by(company_id=user.company_id).order_by(NotificationOutbox.id.desc()).limit(30).all()
    return {'schedule':schedule_view(db.query(SourceRefreshJob).filter_by(company_id=user.company_id).first()),
            'worker_enabled':execution['mode'] == 'worker' and execution['configured'], 'execution':execution,
            'destinations':channels, 'configuration_error':configuration_error,
            'notifications':[{'id':r.id,'event':r.payload.get('event'),'destination_id':r.destination_id,
                'status':r.status,'attempts':r.attempts,'created_at':r.created_at,
                'accepted_at':r.accepted_at,'last_error':r.last_error} for r in recent]}


@router.put('/{source_id}/schedule')
def set_schedule(source_id: str, payload: ScheduleInput, user: User = Depends(require_admin_user), db: Session = Depends(get_db)):
    from app.services.automation_service import configure_schedule
    try:
        return configure_schedule(db, user.company_id, source_id, payload.enabled, payload.interval_seconds, payload.expected_revision)
    except ValueError as error:
        raise HTTPException(503, str(error)) from None


@router.post('/apply')
def apply(payload:ImportInput,user:User=Depends(require_analyst_user),db:Session=Depends(get_db)):
    row=db.query(AnalysisRecord).filter_by(id=payload.preview_id,company_id=user.company_id,kind='import_preview').first()
    if not row: raise HTTPException(404,'Preview is unavailable.')
    if row.content.get('applied'): raise HTTPException(409,'This preview was already imported.')
    if row.dataset_revision!=revision(active(db,user.company_id)): raise HTTPException(409,'Active data changed. Preview this source again.')
    outcome=DataProcessingService(db,user.company_id).process_dataframe(pd.read_csv(io.StringIO(row.content['csv']),dtype=str,keep_default_na=False,na_values=['']),'connected_source.csv',expected_revision=row.dataset_revision or '')
    if outcome.status not in ['success','partial_success']: raise HTTPException(422,outcome.message)
    row.content={'source_id':row.content['source_id'],'rows':row.content['rows'],'applied':True}
    db.commit()
    return {'applied':True,'rows':outcome.processed_rows}
