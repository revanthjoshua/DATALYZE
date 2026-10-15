import pytest
from app.services.reporting_service import ReportingService, csv_text
from app.models.company import Company
from app.models.kpi_definition import KPIDefinition
from app.models.report import Report
from app.core.exceptions import ResourceNotFoundException


def test_exports_are_read_only_and_tenant_scoped(db_session):
    first=Company(name='Export A',industry='Retail',currency='USD')
    second=Company(name='Export B',industry='Retail',currency='USD')
    db_session.add_all([first,second]);db_session.flush()
    kpi=KPIDefinition(company_id=first.id,key='sales',name='=1+1',unit='number',is_active=True)
    db_session.add(kpi);db_session.commit()
    service=ReportingService(db_session,first.id)
    exported=service.generate_kpi_summary_csv()
    assert "'=1+1" in exported
    assert db_session.query(Report).count()==0
    with pytest.raises(ResourceNotFoundException):
        ReportingService(db_session,second.id).generate_kpi_trend_csv(kpi.id)
    assert csv_text('ordinary')=='ordinary'
    assert csv_text('@formula').startswith("'")
