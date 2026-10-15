import io
from app.models.user import User
from app.services.dataset_store import TenantDatasetStore


def admin(client,name):
    r=client.post('/api/v1/auth/register-admin',json={'full_name':name,'phone_number':'+1555111222','email':f'{name}@example.com','username':name,'password':'Password123!','confirm_password':'Password123!','company_name':name,'industry':'Retail/E-commerce'})
    assert r.status_code==201,r.text
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def upload(client,headers,content):
    r=client.post('/api/v1/data/upload',headers=headers,files={'file':('analysis.csv',io.BytesIO(content.encode()),'text/csv')})
    assert r.status_code==200,r.text
    assert r.json()['status'] in ['success','partial_success'],r.text


def test_workspace_evidence_backups_isolation_and_staleness(client,db_session):
    TenantDatasetStore.clear_all()
    a,b=admin(client,'analyst_a'),admin(client,'analyst_b')
    upload(client,a,'key,revenue,region\nA,10,N\nA,10,N\nB,20,S\n')
    p=client.get('/api/v1/analysis/profile',headers=a)
    assert p.status_code==200,p.text
    rev=p.json()['revision']
    brief=client.post('/api/v1/analysis/records',headers=a,json={'kind':'brief','title':'Revenue decision','content':{'question':'Where should we focus?'}})
    assert brief.status_code==201,brief.text
    run=client.post('/api/v1/analysis/run',headers=a,json={'method':'aggregate','parameters':{'metric':'revenue','dimensions':['region']}})
    assert run.status_code==200,run.text
    run_id=run.json()['id']
    assert client.get(f'/api/v1/analysis/records/{run_id}/download',headers=b).status_code==404
    assert client.post('/api/v1/analysis/records',headers=b,json={'kind':'comment','title':'Reply','content':{'parent_id':run_id,'text':'test'}}).status_code==404
    payload={'revision':rev,'operations':[{'operation':'deduplicate'}]}
    preview=client.post('/api/v1/analysis/prepare',headers=a,json=payload)
    assert preview.status_code==200,preview.text
    assert preview.json()['rows_after']==2
    assert client.get('/api/v1/analysis/profile',headers=a).json()['rows']==3
    applied=client.post('/api/v1/analysis/prepare',headers=a,json={**payload,'apply':True})
    assert applied.status_code==200,applied.text
    assert client.get('/api/v1/analysis/profile',headers=a).json()['rows']==2
    docs=client.get('/api/v1/analysis/records',headers=a).json()
    assert next(r for r in docs if r['id']==run_id)['stale'] is True
    assert any(r['kind']=='brief' for r in docs)
    backup=next(r for r in docs if r['kind']=='backup')
    assert backup['content']['rows']==3
    assert client.get(f"/api/v1/analysis/records/{backup['id']}/download",headers=a).text.count('A,10')==2
    assert client.post('/api/v1/analysis/prepare',headers=a,json={**payload,'apply':True}).status_code==409
    assert client.get('/api/v1/analysis/records',headers=b).json()==[]
    user=db_session.query(User).filter(User.username=='analyst_a').first()
    user.role='viewer';db_session.commit()
    assert client.post('/api/v1/analysis/run',headers=a,json={'method':'formula','parameters':{'expression':'revenue'}}).status_code==403
    assert client.get('/api/v1/analysis/profile',headers=a).status_code==200


def test_join_previews_without_overwrite_and_rejects_duplicate_lookup_keys(client):
    TenantDatasetStore.clear_all()
    headers=admin(client,'join_admin')
    upload(client,headers,'key,revenue\nA,10\nB,20\n')
    profile=client.get('/api/v1/analysis/profile',headers=headers)
    assert profile.status_code==200,profile.text
    rev=profile.json()['revision']
    fields={'left_key':'key','right_key':'key','how':'left','dataset_revision':rev,'apply':'false'}
    response=client.post('/api/v1/analysis/join',headers=headers,data=fields,files={'file':('lookup.csv',io.BytesIO(b'key,label\nA,North\nB,South\n'),'text/csv')})
    assert response.status_code==200,response.text
    assert response.json()['matched_rows']==2
    assert response.json()['applied'] is False
    assert 'label' not in [c['name'] for c in client.get('/api/v1/analysis/profile',headers=headers).json()['columns']]
    bad=client.post('/api/v1/analysis/join',headers=headers,data=fields,files={'file':('lookup.csv',io.BytesIO(b'key,label\nA,North\nA,South\n'),'text/csv')})
    assert bad.status_code==422
