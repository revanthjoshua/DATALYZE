import json
import pandas as pd
import pytest
from sqlalchemy import create_engine
from app.models.user import User
from app.services.source_connector_service import fetch_source


@pytest.mark.parametrize('driver,options', [
    ('postgresql', {'connect_timeout': 10}),
    ('postgresql+psycopg2', {'connect_timeout': 10}),
    ('postgresql+psycopg', {'connect_timeout': 10}),
    ('postgresql+pg8000', {'timeout': 10}),
    ('mysql', {'connect_timeout': 10}),
    ('mysql+mysqldb', {'connect_timeout': 10}),
    ('mysql+pymysql', {'connect_timeout': 10}),
    ('mysql+mysqlconnector', {'connection_timeout': 10}),
    ('sqlite', None),
])
def test_database_source_passes_driver_specific_connection_timeout(monkeypatch, driver, options):
    captured = {}
    def unavailable_engine(url, **kwargs):
        captured.update(kwargs)
        raise ConnectionError('Driver details containing private credentials')
    monkeypatch.setattr('app.services.source_connector_service.create_engine', unavailable_engine)
    url = 'sqlite:///:memory:' if driver == 'sqlite' else f'{driver}://reader:fixture-password@example.invalid/source'
    with pytest.raises(ValueError, match='Source could not be read') as error:
        fetch_source({'type': 'database', 'url': url, 'table': 'facts'})
    assert captured == ({'connect_args': options} if options else {})
    assert 'private credentials' not in str(error.value)
    assert 'fixture-password' not in str(error.value)


def test_database_connector_reads_table(tmp_path):
    url='sqlite:///'+str(tmp_path/'source.sqlite')
    engine=create_engine(url)
    pd.DataFrame({'code':['001','002'],'sales':[10,20]}).to_sql('facts',engine,index=False)
    engine.dispose()
    frame=fetch_source({'type':'database','url':url,'table':'facts','columns':['code','sales']})
    assert frame.to_dict('list')=={'code':['001','002'],'sales':[10,20]}


def test_source_import_is_scoped_previewed_and_revision_checked(client,db_session,monkeypatch):
    def register(name):
        r=client.post('/api/v1/auth/register-admin',json={'full_name':name,'phone_number':'+1555111222','email':f'{name}@example.com','username':name,'password':'Password123!','confirm_password':'Password123!','company_name':name,'industry':'Retail/E-commerce'})
        assert r.status_code==201,r.text
        return {'Authorization':'Bearer '+r.json()['access_token']}
    a,b=register('source_a'),register('source_b')
    tenant=db_session.query(User).filter_by(username='source_a').first().company_id
    monkeypatch.setenv('DATALYZE_SOURCES_JSON',json.dumps([{'id':'sales','name':'Sales export','type':'api','url':'https://example.com/private','headers':{'Authorization':'secret-fixture'},'company_ids':[tenant]}]))
    monkeypatch.setattr('app.api.v1.source_routes.fetch_source',lambda _:pd.DataFrame({'code':['001','002'],'sales':[10,20]}))
    assert 'secret-fixture' not in client.get('/api/v1/sources',headers=a).text
    assert client.get('/api/v1/sources',headers=b).json()==[]
    assert client.post('/api/v1/sources/sales/preview',headers=b).status_code==404
    p=client.post('/api/v1/sources/sales/preview',headers=a)
    assert p.status_code==200,p.text
    assert client.get('/api/v1/analysis/profile',headers=a).status_code==404
    payload={'preview_id':p.json()['preview_id']}
    assert client.post('/api/v1/sources/apply',headers=b,json=payload).status_code==404
    applied=client.post('/api/v1/sources/apply',headers=a,json=payload)
    assert applied.status_code==200,applied.text
    assert client.get('/api/v1/analysis/profile',headers=a).json()['rows']==2
    assert client.post('/api/v1/sources/apply',headers=a,json=payload).status_code==409
