from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.core.database import Base
from app.main import readiness


def test_readiness_requires_schema_and_database(monkeypatch):
    engine=create_engine('sqlite:///:memory:',poolclass=StaticPool)
    monkeypatch.setattr('app.main.engine',engine)
    assert readiness().status_code==503
    Base.metadata.create_all(engine)
    assert readiness()['status']=='ready'
    def fail():raise RuntimeError('private connection information')
    monkeypatch.setattr(engine,'connect',fail)
    response=readiness()
    assert response.status_code==503 and b'private' not in response.body
