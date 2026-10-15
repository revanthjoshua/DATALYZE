"""Immutable company reports and accountable stakeholder review."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user, require_analyst_user
from app.models.user import User
from app.models.analysis_record import AnalysisRecord
from app.api.v1.analysis_routes import active, revision
from app.services.evidence_report import evidence_document

router = APIRouter(prefix='/stakeholder-reports', tags=['Stakeholder reports'])
ALLOWED_KINDS = {'brief', 'run', 'finding', 'comment', 'action_update', 'preparation'}


class ReportInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=10000)
    record_ids: list[int] = Field(min_length=1, max_length=20)


class ReviewInput(BaseModel):
    decision: Literal['Reviewed', 'Changes requested', 'Approved']
    comment: str = Field(min_length=1, max_length=5000)


def report_or_404(db, user, report_id):
    report = db.query(AnalysisRecord).filter_by(id=report_id, company_id=user.company_id, kind='stakeholder_report').first()
    if report is None:
        raise HTTPException(404, 'Report not found in this workspace.')
    return report


def metadata(row, current):
    return {'id':row.id, 'title':row.title, 'created_at':row.created_at.replace(tzinfo=timezone.utc).isoformat(),
            'author_id':row.user_id, 'summary':row.content['summary'],
            'record_count':len(row.content['evidence']), 'historical':any(
                e.get('dataset_revision') and e['dataset_revision'] != current for e in row.content['evidence'])}


@router.get('')
def listing(user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    current = revision(active(db,user.company_id))
    rows = db.query(AnalysisRecord).filter_by(company_id=user.company_id,kind='stakeholder_report').order_by(AnalysisRecord.id.desc()).limit(100).all()
    return [metadata(row,current) for row in rows]


@router.post('',status_code=201)
def create_report(payload:ReportInput,user:User=Depends(require_analyst_user),db:Session=Depends(get_db)):
    ids = list(dict.fromkeys(payload.record_ids))
    found = db.query(AnalysisRecord).filter(AnalysisRecord.company_id==user.company_id,
        AnalysisRecord.id.in_(ids),AnalysisRecord.kind.in_(ALLOWED_KINDS)).all()
    if len(found) != len(ids):
        raise HTTPException(404,'Choose only available evidence and findings from this company.')
    mapping = {r.id:r for r in found}
    evidence = [{'record_id':r.id,'title':r.title,'kind':r.kind,'author_id':r.user_id,
        'created_at':r.created_at.replace(tzinfo=timezone.utc).isoformat(),'dataset_revision':r.dataset_revision,'content':r.content}
        for r in (mapping[i] for i in ids)]
    content = {'summary':payload.summary.strip(),'evidence':evidence,
        'audience':'Authenticated members of this company; invite external stakeholders with a Viewer role.'}
    if not payload.title.strip() or not content['summary']:
        raise HTTPException(422,'Enter a report title and summary.')
    if len(json.dumps(content).encode()) > 2*1024*1024:
        raise HTTPException(413,'Select fewer records; a report supports up to 2 MB of evidence.')
    row = AnalysisRecord(company_id=user.company_id,user_id=user.id,kind='stakeholder_report',
        title=payload.title.strip(),content=content,dataset_revision=revision(active(db,user.company_id)))
    db.add(row); db.commit(); db.refresh(row)
    return metadata(row,revision(active(db,user.company_id)))


@router.get('/{report_id}')
def detail(report_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row = report_or_404(db,user,report_id)
    reviews = db.query(AnalysisRecord).filter_by(company_id=user.company_id,kind='report_review').order_by(AnalysisRecord.id).all()
    return {**metadata(row,revision(active(db,user.company_id))), 'content':row.content,
        'reviews':[{'id':r.id,'author_id':r.user_id,'created_at':r.created_at.replace(tzinfo=timezone.utc).isoformat(),**r.content}
                   for r in reviews if r.content.get('report_id')==row.id]}


@router.post('/{report_id}/reviews',status_code=201)
def review(report_id:int,payload:ReviewInput,user:User=Depends(require_analyst_user),db:Session=Depends(get_db)):
    report = report_or_404(db,user,report_id)
    if not payload.comment.strip(): raise HTTPException(422,'Explain the review decision.')
    row=AnalysisRecord(company_id=user.company_id,user_id=user.id,kind='report_review',
        title=f'Review: {report.title}'[:200],content={'report_id':report.id,**payload.model_dump()},
        dataset_revision=report.dataset_revision)
    db.add(row);db.commit();db.refresh(row)
    return {'id':row.id,'author_id':user.id,**row.content}


@router.get('/{report_id}/download')
def download(report_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=report_or_404(db,user,report_id)
    payload=detail(report_id,user,db)
    document=evidence_document(SimpleNamespace(id=row.id,title=row.title,created_at=row.created_at,
        user_id=row.user_id,dataset_revision=row.dataset_revision,
        content={**row.content,'reviews':payload['reviews']}),payload['historical'])
    return Response(document,media_type='text/html',headers={
        'Content-Disposition':f'attachment; filename="datalyze-report-{row.id}.html"',
        'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
