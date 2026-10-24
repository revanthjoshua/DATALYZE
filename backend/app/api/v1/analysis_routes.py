from app.services.evidence_report import evidence_document
from app.services.payload_limits import check_response_size
import html
import io
import os
import json
from datetime import datetime, timezone
from typing import Any, Literal
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.analysis_record import AnalysisRecord
from app.models.uploaded_dataset import UploadedDataset
from app.models.user import User
from app.middleware.auth_middleware import get_current_user, require_analyst_user
from app.api.v1.data_routes import _ensure_dataset_loaded
from app.services.dataset_store import TenantDatasetStore
from app.services.data_ingestion_service import DataIngestionService
from app.services.data_processing_service import DataProcessingService
from app.services.analyst_service import AnalystService, records

router = APIRouter(prefix='/analysis', tags=['Analyst workspace'])


def active(db, tenant):
    return db.query(UploadedDataset).filter(UploadedDataset.company_id == tenant).order_by(UploadedDataset.created_at.desc()).first()


def revision(dataset):
    return f'{dataset.id}:{dataset.file_hash}' if dataset else None


def source(db, user):
    dataset = active(db, user.company_id)
    if not dataset:
        raise HTTPException(404, 'Upload a dataset before running analysis.')
    # Every analytical request uses current persisted data, including across workers.
    TenantDatasetStore.clear_dataset(user.company_id)
    frame = _ensure_dataset_loaded(user.company_id, db)
    if frame is None or frame.empty:
        raise HTTPException(409, 'The stored dataset is unavailable.')
    return dataset, AnalystService(frame)


def present(row, current):
    return {'id':row.id, 'kind':row.kind, 'title':row.title, 'user_id':row.user_id,
            'created_at':row.created_at.replace(tzinfo=timezone.utc).isoformat(), 'dataset_revision':row.dataset_revision,
            'stale': bool(row.dataset_revision and row.dataset_revision != current),
            'content':row.content if row.kind != 'backup' else {'filename':row.content['filename'], 'rows':row.content['rows']}}


def insert(db, user, kind, title, content, rev=None):
    row = AnalysisRecord(company_id=user.company_id, user_id=user.id, kind=kind, title=title,
                         content=content, dataset_revision=rev)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get('/profile')
def profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset, service = source(db,user)
    return {'revision':revision(dataset), 'filename':dataset.filename, **service.profile()}


class NoteInput(BaseModel):
    kind: Literal['brief','finding','comment','monitor','metric_rule']
    title: str = Field(min_length=1, max_length=200)
    content: dict[str, Any]


@router.get('/records')
def list_records(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current = revision(active(db,user.company_id))
    rows = db.query(AnalysisRecord).filter(AnalysisRecord.company_id == user.company_id, AnalysisRecord.kind.notin_(['import_preview','saved_dataset','dataset_state','stakeholder_report','report_review','monitor_attempt'])).order_by(AnalysisRecord.id.desc()).limit(200).all()
    return [present(row,current) for row in rows]


@router.post('/records', status_code=201)
def save_note(payload: NoteInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    if len(json.dumps(payload.content)) > 30000:
        raise HTTPException(422,'Keep notes under 30,000 characters.')
    if payload.kind == 'comment':
        parent = db.query(AnalysisRecord).filter(AnalysisRecord.company_id == user.company_id, AnalysisRecord.id == payload.content.get('parent_id')).first()
        if not parent: raise HTTPException(404,'The referenced finding is not available in this workspace.')
    if payload.kind == 'finding' and payload.content.get('evidence_id') is not None:
        evidence = db.query(AnalysisRecord).filter_by(company_id=user.company_id, id=payload.content['evidence_id'], kind='run').first()
        if not evidence: raise HTTPException(404,'The selected evidence is not available in this workspace.')
    if payload.kind == 'metric_rule':
        _,service = source(db,user)
        try:
            expression = payload.content['expression']
            service.formula(expression)
            target = float(payload.content['target'])
            if not pd.notna(target) or abs(target) == float('inf'): raise ValueError()
            aggregation = payload.content.get('aggregation','sum')
            direction = payload.content.get('direction','at_least')
            if aggregation not in ['sum','mean'] or direction not in ['at_least','at_most']: raise ValueError()
            payload.content = {'expression':expression,'target':target,'aggregation':aggregation,'direction':direction}
        except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError,OverflowError):
            raise HTTPException(422,'Provide a valid formula, a finite numeric target, sum or mean, and a target direction.')
    if payload.kind == 'monitor':
        try:
            hours = float(payload.content.get('max_age_hours',24))
            missing = float(payload.content.get('max_missing_percent',10))
            if not 1 <= hours <= 8760 or not 0 <= missing <= 100: raise ValueError()
        except (ValueError,TypeError): raise HTTPException(422,'Choose freshness from 1–8,760 hours and missing values from 0–100%.')
        payload.content = {'max_age_hours':hours, 'max_missing_percent':missing}
    rev = revision(active(db,user.company_id)) if payload.kind in ['finding','comment'] else None
    return present(insert(db,user,payload.kind,payload.title,payload.content,rev), rev)


@router.get('/metrics')
def metrics(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dataset,service=source(db,user)
    rules=db.query(AnalysisRecord).filter_by(company_id=user.company_id,kind='metric_rule').order_by(AnalysisRecord.id.desc()).limit(100).all()
    result=[]
    for rule in rules:
        entry={'id':rule.id,'name':rule.title,**rule.content,'revision':revision(dataset)}
        try:
            values=service.formula(rule.content['expression'])
            value=values[rule.content['aggregation']]
            met=None if value is None else (value>=rule.content['target'] if rule.content['direction']=='at_least' else value<=rule.content['target'])
            entry.update(value=value,target_met=met,valid_rows=values['valid_rows'],undefined_rows=values['undefined_rows'])
        except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError,OverflowError):
            entry.update(value=None,target_met=None,error='Formula is unavailable for the current dataset. Review its columns.')
        result.append(entry)
    return result


class ActionUpdate(BaseModel):
    status: Literal['Proposed','Approved','In progress','Completed','Rejected']
    outcome: str = Field(default='',max_length=5000)


@router.post('/records/{record_id}/progress')
def progress(record_id:int,payload:ActionUpdate,user:User=Depends(require_analyst_user),db:Session=Depends(get_db)):
    row=db.query(AnalysisRecord).filter_by(id=record_id,company_id=user.company_id,kind='finding').first()
    if not row: raise HTTPException(404,'Finding not found.')
    event=insert(db,user,'action_update',f'Action update: {row.title}'[:200],{'parent_id':row.id,'status':payload.status,'outcome':payload.outcome},row.dataset_revision)
    return present(event,revision(active(db,user.company_id)))


class RunInput(BaseModel):
    method: Literal['aggregate','formula','compare','investigate','trend']
    title: str = Field(default='Analysis', min_length=1, max_length=200)
    parameters: dict[str,Any]


@router.post('/run')
def run(payload: RunInput, user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    dataset, service = source(db,user)
    try:
        result = getattr(service,payload.method)(**payload.parameters)
        # Reject non-JSON numeric results before saving evidence.
        json.dumps(result, allow_nan=False)
    except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError,OverflowError) as error:
        raise HTTPException(422,str(error))
    content = {'method':payload.method, 'parameters':payload.parameters, 'source_filename':dataset.filename, 'result':result}
    return present(insert(db,user,'run',payload.title,content,revision(dataset)), revision(dataset))


class PreparationInput(BaseModel):
    operations: list[dict[str,Any]] = Field(max_length=20)
    revision: str
    apply: bool = False


def backup(db,user,dataset,frame):
    data = frame[[c for c in frame if not str(c).startswith('_')]].to_csv(index=False)
    if len(data.encode()) > 20*1024*1024:
        raise HTTPException(413,'Preparation backups support up to 20 MB. Download and prepare this larger dataset externally.')
    insert(db,user,'backup',f'Before preparation: {dataset.filename}'[:200], {'filename':dataset.filename,'rows':len(frame),'csv':data},revision(dataset))


@router.post('/prepare')
def prepare(payload: PreparationInput,user: User = Depends(require_analyst_user),db: Session = Depends(get_db)):
    dataset,service = source(db,user)
    if payload.revision != revision(dataset): raise HTTPException(409,'Dataset changed. Preview preparation again.')
    try: result,audit = service.prepare(payload.operations)
    except (ValueError,TypeError,KeyError) as error: raise HTTPException(422,str(error))
    response = {'rows_before':len(service.frame), 'rows_after':len(result), 'audit':audit, 'preview':records(result.head(30)), 'applied':False}
    if payload.apply:
        outcome = DataProcessingService(db,user.company_id).process_dataframe(result,dataset.filename,expected_revision=payload.revision)
        if outcome.status not in ['success','partial_success']: raise HTTPException(422,outcome.message)
        insert(db,user,'preparation','Preparation applied', {'steps':payload.operations, 'audit':audit}, revision(active(db,user.company_id)))
        response['applied'] = True
    return response


@router.post('/join')
async def join(file: UploadFile = File(...), left_key: str = Form(...), right_key: str = Form(...),
               how: str = Form('left'), cardinality: str = Form('many_to_one'), dataset_revision: str = Form(...), apply: bool = Form(False),
               user: User = Depends(require_analyst_user), db: Session = Depends(get_db)):
    dataset,service = source(db,user)
    if dataset_revision != revision(dataset): raise HTTPException(409,'Dataset changed. Preview the join again.')
    if how not in ['left','inner','outer']: raise HTTPException(422,'Choose left, inner or outer join.')
    right,filename = await DataIngestionService(user.company_id).read_uploaded_file(file)
    left = service.frame
    try:
        result, diagnostics = service.join(right,left_key,right_key,how=how,cardinality=cardinality)
    except (ValueError,TypeError,KeyError) as error:
        raise HTTPException(422,str(error))
    matched = diagnostics['matched_rows']
    response = {**diagnostics, 'rows_before':len(left), 'rows_after':len(result), 'preview':records(result.head(30)), 'applied':False}
    if apply:
        outcome = DataProcessingService(db,user.company_id).process_dataframe(result,'joined_dataset.csv',expected_revision=dataset_revision)
        if outcome.status not in ['success','partial_success']: raise HTTPException(422,outcome.message)
        insert(db,user,'preparation','Join applied',{'lookup_filename':filename,'left_key':left_key,'right_key':right_key,'how':how,'matched_rows':matched},revision(active(db,user.company_id)))
        response['applied'] = True
    return response


@router.get('/records/{record_id}/download')
def download(record_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row = db.query(AnalysisRecord).filter(AnalysisRecord.id==record_id,AnalysisRecord.company_id==user.company_id).first()
    if not row: raise HTTPException(404,'Record not found.')
    if row.kind == 'backup':
        check_response_size(row.content['csv'], 'This backup download')
        return Response(row.content['csv'],media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="dataset-backup-{row.id}.csv"'})
    if row.kind in ['import_preview','saved_dataset','dataset_state','stakeholder_report','report_review','monitor_attempt']: raise HTTPException(404,'Record not found.')
    stale = bool(row.dataset_revision and row.dataset_revision != revision(active(db,user.company_id)))
    document = evidence_document(row, stale)
    check_response_size(document, 'This evidence report download')
    return Response(document,media_type='text/html',headers={'Content-Disposition':f'attachment; filename="datalyze-brief-{row.id}.html"'})


@router.get('/monitor')
def monitor(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dataset,service = source(db,user)
    rule = db.query(AnalysisRecord).filter(AnalysisRecord.company_id==user.company_id,AnalysisRecord.kind=='monitor').order_by(AnalysisRecord.id.desc()).first()
    limits = rule.content if rule else {'max_age_hours':24,'max_missing_percent':10}
    created = dataset.created_at.replace(tzinfo=timezone.utc) if dataset.created_at.tzinfo is None else dataset.created_at
    age = max(0,(datetime.now(timezone.utc)-created).total_seconds()/3600)
    df=service.frame
    missing = float(df.isna().sum().sum()/max(1,df.size)*100)
    checks=[{'name':'Upload freshness','value':round(age,2),'unit':'hours','threshold':float(limits['max_age_hours']),'alert':age>float(limits['max_age_hours'])},
            {'name':'Missing cells','value':round(missing,2),'unit':'%','threshold':float(limits['max_missing_percent']),'alert':missing>float(limits['max_missing_percent'])}]
    for target in metrics(user,db):
        checks.append({'name':f"Metric target #{target['id']}: {target['name']}",
            'value':target.get('value'),'unit':target['direction'],'threshold':target['target'],
            'alert':target.get('target_met') is not True})
    latest=db.query(AnalysisRecord).filter_by(company_id=user.company_id,kind='monitor_check').order_by(AnalysisRecord.id.desc()).first()
    from app.services.monitor_runner import scheduler_configuration
    execution = scheduler_configuration()
    attempt = db.query(AnalysisRecord).filter_by(company_id=user.company_id,kind='monitor_attempt').order_by(AnalysisRecord.id.desc()).first()
    return {'checked_at':datetime.now(timezone.utc).isoformat(),'revision':revision(dataset),'checks':checks,
            'background':{**execution, 'last_check':latest.content.get('checked_at') if latest else None,
                'last_attempt':attempt.content if attempt else None},
            'mode':execution['description'] + ' This view also refreshes every 60 seconds while open.'}
