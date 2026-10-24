import io
import pandas as pd
from datetime import datetime, timedelta
from app.models.company import Company
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.models.prediction import Prediction
from app.repositories.kpi_repository import KPIRepository
from app.services.data_processing_service import DataProcessingService
from app.services.dataset_store import TenantDatasetStore
from app.api.v1.data_routes import _ensure_dataset_loaded


def test_missing_values_stay_missing_and_undated_data_is_not_forecast(db_session):
    company = Company(name='Integrity', industry='Retail', currency='USD')
    db_session.add(company)
    db_session.commit()
    data = pd.DataFrame({'record_id': ['A', 'B', 'C', 'D', 'E', 'F'], 'revenue': [1., 2., None, 4., 5., 6.]})
    result = DataProcessingService(db_session, company.id).process_dataframe(data, 'source.xlsx')
    assert result.status == 'success'
    stored = TenantDatasetStore.get_dataset(company.id)
    assert pd.isna(stored.iloc[2]['revenue'])
    assert db_session.query(Prediction).filter(Prediction.company_id == company.id).count() == 0
    TenantDatasetStore.clear_dataset(company.id)
    restored = _ensure_dataset_loaded(company.id, db_session)
    assert restored is not None
    assert len(restored) == 6
    assert pd.isna(restored.iloc[2]['revenue'])


def test_history_returns_latest_window_in_chronological_order(db_session):
    company = Company(name='History', industry='Retail', currency='USD')
    db_session.add(company)
    db_session.flush()
    kpi = KPIDefinition(company_id=company.id, key='revenue', name='Revenue', unit='number')
    db_session.add(kpi)
    db_session.flush()
    for i in range(220):
        db_session.add(KPIValue(company_id=company.id, kpi_id=kpi.id, timestamp=datetime(2025,1,1)+timedelta(days=i), value=i))
    db_session.commit()
    values = KPIRepository(db_session, company.id).get_kpi_values(kpi.id, limit=10)
    assert [v.value for v in values] == list(range(210,220))


def test_persisted_revision_replaces_stale_worker_cache(db_session):
    company=Company(name='Cache',industry='Retail',currency='USD')
    db_session.add(company);db_session.commit()
    DataProcessingService(db_session,company.id).process_dataframe(pd.DataFrame({'key':['001','002'],'amount':[10,20]}),'facts.csv')
    current=_ensure_dataset_loaded(company.id,db_session)
    assert current['amount'].tolist()==[10,20]
    TenantDatasetStore.set_dataset(company.id,pd.DataFrame({'amount':[999]}),revision='stale-worker')
    restored=_ensure_dataset_loaded(company.id,db_session)
    assert restored['amount'].tolist()==[10,20]
    assert restored['key'].tolist()==['001','002']
