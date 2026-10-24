import pandas as pd
import pytest
from app.ml.root_cause.contribution_analyzer import ContributionAnalyzer


def test_undated_data_does_not_generate_causal_evidence():
    df=pd.DataFrame({'region':['N','N','S','S'],'revenue':[100,100,20,20]})
    assert ContributionAnalyzer.analyze_from_dataset(df,'revenue',['region']) == []


def test_equal_observed_contributions_remain_equal():
    results=ContributionAnalyzer.analyze_dimension_contributions({'region':{'N':50,'S':50}},{'region':{'N':100,'S':100}},100,'down')
    assert [r['contribution_percentage'] for r in results]==[50,50]
    assert all(r['confidence_score'] is None for r in results)
    assert sum(r['contribution_percentage'] for r in results)==100


def test_string_labels_do_not_become_fake_measurements():
    assert ContributionAnalyzer.analyze_dimension_contributions({'region':'North'},{},100,'down')==[]


def test_dated_contributions_reconcile():
    df=pd.DataFrame({'date':['2026-01-01','2026-01-01','2026-01-02','2026-01-02'],'region':['N','S','N','S'],'revenue':[100,100,40,60]})
    result=ContributionAnalyzer.analyze_from_dataset(df,'revenue',['region'],date_col='date',split_date='2026-01-02')
    assert sorted(r['contribution_percentage'] for r in result)==[40,60]
