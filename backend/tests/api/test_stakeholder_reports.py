from app.models.company import Company
from app.models.user import User
from app.models.analysis_record import AnalysisRecord
from app.core.security import create_access_token


def seed(db):
    a,b=Company(name='Report company'),Company(name='Other company')
    db.add_all([a,b]);db.flush()
    writer=User(company_id=a.id,email='report-writer@example.com',full_name='Writer',hashed_password='unused',role='analyst')
    viewer=User(company_id=a.id,email='report-viewer@example.com',full_name='Viewer',hashed_password='unused',role='viewer')
    outsider=User(company_id=b.id,email='report-outsider@example.com',full_name='Outsider',hashed_password='unused',role='company admin')
    db.add_all([writer,viewer,outsider]);db.flush()
    note=AnalysisRecord(company_id=a.id,user_id=writer.id,kind='finding',title='<script>unsafe()</script>',content={'text':'Original evidence','status':'Proposed'})
    db.add(note);db.commit()
    def headers(u):return {'Authorization':'Bearer '+create_access_token({'sub':str(u.id)})}
    return writer,note,headers(writer),headers(viewer),headers(outsider)


def test_report_snapshot_review_export_and_tenant_boundaries(client,db_session):
    writer,note,headers,viewer,other=seed(db_session)
    payload={'title':'Decision brief','summary':'<img src=x onerror=alert(1)>','record_ids':[note.id]}
    assert client.post('/api/v1/stakeholder-reports',headers=viewer,json=payload).status_code==403
    response=client.post('/api/v1/stakeholder-reports',headers=headers,json=payload)
    assert response.status_code==201,response.text
    id=response.json()['id']
    note.content={'text':'Changed afterwards'};db_session.commit()
    report=client.get(f'/api/v1/stakeholder-reports/{id}',headers=viewer)
    assert report.json()['content']['evidence'][0]['content']['text']=='Original evidence'
    for path in [f'/{id}',f'/{id}/download']:
        assert client.get('/api/v1/stakeholder-reports'+path,headers=other).status_code==404
    assert client.get('/api/v1/stakeholder-reports',headers=other).json()==[]
    review={'decision':'Changes requested','comment':'Validate the proposed action with the owner.'}
    assert client.post(f'/api/v1/stakeholder-reports/{id}/reviews',headers=viewer,json=review).status_code==403
    assert client.post(f'/api/v1/stakeholder-reports/{id}/reviews',headers=headers,json=review).status_code==201
    exported=client.get(f'/api/v1/stakeholder-reports/{id}/download',headers=viewer)
    assert exported.status_code==200 and exported.headers['cache-control']=='no-store'
    assert '<script>' not in exported.text and '<img src=x' not in exported.text
    assert '&lt;script&gt;' in exported.text and 'Changes requested' in exported.text
    assert client.get(f'/api/v1/stakeholder-reports/{id}').status_code==401


def test_reports_reject_foreign_raw_snapshots_and_empty_summaries(client,db_session):
    writer,note,headers,viewer,other=seed(db_session)
    raw=AnalysisRecord(company_id=writer.company_id,user_id=writer.id,kind='saved_dataset',title='Private source',content={'snapshot':'raw data'})
    db_session.add(raw);db_session.commit()
    assert client.post('/api/v1/stakeholder-reports',headers=headers,json={'title':'Report','summary':'Summary','record_ids':[raw.id]}).status_code==404
    assert client.post('/api/v1/stakeholder-reports',headers=other,json={'title':'Report','summary':'Summary','record_ids':[note.id]}).status_code==404
    assert client.post('/api/v1/stakeholder-reports',headers=headers,json={'title':'Report','summary':' ','record_ids':[note.id]}).status_code==422
