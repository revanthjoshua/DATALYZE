import numpy as np
import pandas as pd
import pytest
from app.services.analyst_service import AnalystService


def test_profile_and_preparation_preserve_source():
    df=pd.DataFrame({'name':[' A ',' A ','B'], 'revenue':[1.,1.,None]})
    service=AnalystService(df)
    profile=service.profile()
    assert profile['duplicates']==1
    assert profile['missing_cells']==1
    result,audit=service.prepare([{'operation':'trim','column':'name'},{'operation':'deduplicate'},{'operation':'fill_median','column':'revenue'}])
    assert list(result.name)==['A','B']
    assert list(result.revenue)==[1.,1.]
    assert len(df)==3 and pd.isna(df.iloc[2].revenue)
    assert audit[1]['rows_after']==2


def test_formula_is_safe_and_tracks_undefined_ratios():
    service=AnalystService(pd.DataFrame({'revenue':[100.,0.,None],'cost':[60.,10.,20.]}))
    result=service.formula('(revenue - cost) / revenue * 100')
    assert result['mean']==40
    assert result['undefined_rows']==2
    with pytest.raises(ValueError): service.formula('__import__("os").getcwd()')
    with pytest.raises(ValueError): service.formula('revenue ** 1000000')


def test_aggregation_does_not_turn_missing_group_into_zero():
    service=AnalystService(pd.DataFrame({'region':['N','N','S'],'value':[1.,2.,None]}))
    rows=service.aggregate('value',['region'])['rows']
    assert rows[0]=={'region':'N','value':3.}
    assert rows[1]['value'] is None


def test_statistical_comparison_reports_measured_effect_and_uncertainty():
    service=AnalystService(pd.DataFrame({'group':['A']*20+['B']*20,'value':list(range(20))+list(range(20,40))}))
    result=service.compare('value','group','A','B')
    assert result['mean_difference']==20
    assert result['p_value']<0.01
    assert result['confidence_interval_95'][0]>0
    with pytest.raises(ValueError):service.compare('value','group','A','A')


def test_contributions_reconcile_to_normalized_period_change():
    service=AnalystService(pd.DataFrame({'date':['2026-01-01','2026-01-01','2026-01-02','2026-01-02'], 'region':['N','S','N','S'],'value':[10,20,30,15]}))
    result=service.investigate('value','date','region','2026-01-02')
    assert result['net_change']==15
    assert sum(r['change'] for r in result['rows'])==15
    assert result['rows'][0]['segment']=='N'


def test_forecast_backtest_and_real_date_requirements():
    service=AnalystService(pd.DataFrame({'date':pd.date_range('2026-01-01',periods=30),'value':np.arange(30.)*2+10}))
    result=service.trend('value','date')
    assert result['method']=='Linear trend'
    assert result['forecast'][0]['value']==pytest.approx(70.)
    assert result['validation_observations']>=3
    assert len(result['history'])==30
    broken=service.frame.drop(index=10)
    with pytest.raises(ValueError,match='gaps'):AnalystService(broken).trend('value','date')
    with pytest.raises(ValueError,match='12'):AnalystService(service.frame.head(4)).trend('value','date')


def test_formula_scalar_division_and_invalid_inputs_have_consistent_results():
    service = AnalystService(pd.DataFrame({'value':[1., 2.]}))
    assert service.formula('1 / 0')['undefined_rows'] == 2
    assert service.formula('value / (1 / 0)')['undefined_rows'] == 2
    assert service.formula('value / (1e308 * 1e308)')['sum'] is None
    with pytest.raises(ValueError, match='syntax'):
        service.formula('value +')
    with pytest.raises(ValueError, match='distinct'):
        service.aggregate('value', ['value'])
    with pytest.raises(ValueError, match='object'):
        service.prepare([None])


def test_imputation_does_not_replace_unparsed_source_values_without_explicit_conversion():
    service = AnalystService(pd.DataFrame({'amount':['3', 'pending', None]}))
    with pytest.raises(ValueError, match='explicitly'):
        service.prepare([{'operation':'fill_mean', 'column':'amount'}])
    _, audit = service.prepare([{'operation':'numeric', 'column':'amount'}])
    assert audit[0]['missing_before'] == 1
    assert audit[0]['missing_after'] == 2


def test_forecast_detects_break_from_constant_history_and_does_not_interpret_ids_as_dates():
    service = AnalystService(pd.DataFrame({'date':pd.date_range('2026-01-01', periods=12), 'value':[5.]*11+[20.]}))
    result = service.trend('value','date')
    assert result['history'][-1]['anomaly'] is True
    with pytest.raises(ValueError, match='numeric'):
        AnalystService(pd.DataFrame({'date':range(12), 'value':range(12)})).trend('value', 'date')
    with pytest.raises(ValueError, match='Horizon'):
        service.trend('value', 'date', True)
