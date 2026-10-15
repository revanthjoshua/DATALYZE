import numpy as np
import pandas as pd
import pytest
from app.services.analyst_service import AnalystService


def test_sequential_transforms_derive_all_rows_and_preserve_source():
    data=pd.DataFrame({'label':[' A ',' B ']*75,'revenue':range(150),'cost':[1]*150,'date':['2026-01-03']*150})
    result,audit=AnalystService(data).prepare([
        {'operation':'trim','column':'label'},{'operation':'lower','column':'label'},
        {'operation':'derive','expression':'revenue-cost','output':'margin'},
        {'operation':'rename','column':'margin','value':'profit'},
        {'operation':'filter','column':'profit','operator':'gte','value':'100'},
        {'operation':'date_part','column':'date','part':'month','output':'month'},
        {'operation':'sort','column':'profit','direction':'desc'}])
    assert len(result)==49 and result.profit.iloc[0]==148
    assert result.month.eq(1).all() and set(result.label)=={'a','b'}
    assert 'profit' not in data and len(audit)==7
    with pytest.raises(ValueError):AnalystService(data).prepare([{'operation':'rename','column':'cost','value':'revenue'}])


def test_join_cardinality_composite_keys_and_expansion_guard():
    left=pd.DataFrame({'id':['001','001','002'],'region':['N','S','S'],'value':[1,2,3]})
    right=pd.DataFrame({'id':['001','001','002'],'region':['N','S','S'],'name':['a','b','c']})
    result,audit=AnalystService(left).join(right,['id','region'],['id','region'])
    assert result.name.tolist()==['a','b','c'] and audit['matched_rows']==3
    with pytest.raises(ValueError,match='unique'):AnalystService(left).join(right,'id','id')
    _,audit=AnalystService(left).join(right,'id','id',cardinality='many_to_many')
    assert audit['rows_after']==5
    with pytest.raises(ValueError,match='100,000'):
        AnalystService(pd.DataFrame({'k':[1]*400})).join(pd.DataFrame({'k':[1]*400}),'k','k',cardinality='many_to_many')
    with pytest.raises(ValueError,match='nonmissing'):
        AnalystService(left).join(pd.DataFrame({'id':[None],'n':[1]}),'id','id')


def test_weekly_forecast_wins_against_baselines_and_exposes_horizon_validation():
    pattern=np.array([10,20,30,40,50,100,150],dtype=float)
    service=AnalystService(pd.DataFrame({'date':pd.date_range('2026-01-01',periods=84),'value':np.tile(pattern,12)}))
    result=service.trend('value','date',14)
    assert result['method']=='Weekly seasonal'
    assert [r['value'] for r in result['forecast']]==list(np.tile(pattern,2))
    assert result['backtest_mae']['Weekly seasonal']==0
    assert result['validation_by_horizon'][-1]['samples']>=3
    small=AnalystService(service.frame.head(12)).trend('value','date',30)
    assert small['validation_by_horizon'][-1]['samples']==0
    assert 'Sparse' in small['validation_by_horizon'][-1]['range_method']


def test_investigation_volume_value_reconciles_and_bounds_are_explicit():
    frame=pd.DataFrame({'date':['2026-01-01']*2+['2026-01-03']*4,'segment':['A']*6,'value':[10,10,15,15,15,15]})
    result=AnalystService(frame).investigate('value','date','segment','2026-01-03',baseline_start_date='2026-01-01',comparison_end_date='2026-01-04')
    row=result['rows'][0]
    assert row['change']==40
    assert row['row_volume_component']+row['row_value_component']==40
    assert result['coverage'][0]['missing_calendar_days']==1
    assert result['coverage'][1]['missing_calendar_days']==1
    with pytest.raises(ValueError):AnalystService(frame).investigate('value','date','segment','2026-01-03',comparison_end_date='2025-01-01')
