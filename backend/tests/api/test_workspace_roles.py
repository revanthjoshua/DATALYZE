import pytest
from app.models.company import Company
from app.models.user import User
from app.core.security import create_access_token


@pytest.mark.parametrize('role,writes,admin',[
    ('Company Admin',True,True),('Platform Super Admin',True,True),('Manager',True,False),
    ('Analyst',True,False),('Employee',True,False),('Viewer',False,False),('unrecognized',False,False)])
def test_workspace_role_matrix(client,db_session,role,writes,admin):
    company=Company(name='Role matrix');db_session.add(company);db_session.flush()
    user=User(company_id=company.id,email='matrix@example.com',full_name='Role Tester',hashed_password='unused',role=role)
    db_session.add(user);db_session.commit()
    headers={'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}
    for path in ['/analysis/records','/datasets','/stakeholder-reports','/sources/automation/status','/company','/auth/me']:
        assert client.get('/api/v1'+path,headers=headers).status_code==200,(role,path)
    note={'kind':'brief','title':'Decision','content':{'question':'Which change needs review?'}}
    assert client.post('/api/v1/analysis/records',headers=headers,json=note).status_code==(201 if writes else 403)
    assert client.get('/api/v1/company/invitations',headers=headers).status_code==(200 if admin else 403)
    assert client.put('/api/v1/company',headers=headers,json={'name':'Updated role matrix'}).status_code==(200 if admin else 403)
