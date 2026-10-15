from datetime import datetime, timedelta
import pandas as pd
import pytest
from app.models.company import Company
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.models.uploaded_dataset import UploadedDataset
from app.repositories.dataset_repository import DatasetRepository
from app.services.data_processing_service import DataProcessingService
from app.services.kpi_service import KPIService
from app.schemas.kpi_schema import KPIDefinitionCreate, KPIDefinitionUpdate
from app.api.v1.data_routes import _ensure_dataset_loaded
from app.services.dataset_store import TenantDatasetStore


def test_failed_replacement_preserves_original_data_and_metrics(db_session, monkeypatch):
    company = Company(name='Atomic', industry='Retail', currency='USD')
    db_session.add(company); db_session.commit()
    service = DataProcessingService(db_session, company.id)
    service.process_dataframe(pd.DataFrame({'item':['A','B'], 'revenue':[10,20]}), 'original.csv')
    original = db_session.query(UploadedDataset).filter_by(company_id=company.id).first().file_hash
    def fail(*args, **kwargs):
        raise RuntimeError('Injected metadata failure')
    monkeypatch.setattr(DatasetRepository, 'record_dataset', fail)
    with pytest.raises(RuntimeError, match='Injected'):
        service.process_dataframe(pd.DataFrame({'item':['C'], 'revenue':[900]}), 'replacement.csv')
    assert db_session.query(UploadedDataset).filter_by(company_id=company.id).first().file_hash == original
    assert [v.value for v in db_session.query(KPIValue).filter_by(company_id=company.id).order_by(KPIValue.id)] == [10,20]
    TenantDatasetStore.clear_dataset(company.id)
    assert _ensure_dataset_loaded(company.id, db_session)['revenue'].tolist() == [10,20]


def test_kpi_mutations_and_observed_date_filter(db_session):
    company = Company(name='Metric controls', industry='Retail', currency='USD')
    db_session.add(company); db_session.commit()
    service = KPIService(db_session, company.id)
    kpi = service.create_custom_kpi(KPIDefinitionCreate(key='measure', name='Measure', unit='number'))
    assert service.update_kpi(kpi.id, KPIDefinitionUpdate(name='Edited')).name == 'Edited'
    assert not service.toggle_kpi_status(kpi.id, False).is_active
    service.toggle_kpi_status(kpi.id, True)
    for i in range(40):
        db_session.add(KPIValue(company_id=company.id,kpi_id=kpi.id,timestamp=datetime(2020,1,1)+timedelta(days=i),value=i))
    db_session.commit()
    assert len(service.get_dashboard_kpi_summaries(days=7)[0].recent_history) == 7
    assert len(service.get_dashboard_kpi_summaries()[0].recent_history) == 40
