"""Exercise the analyst journey against actual persisted uploads in three formats."""
import io
import json
from datetime import datetime, timedelta, timezone
from html import escape

import pandas as pd
import pytest

from app.models.analysis_record import AnalysisRecord
from app.models.uploaded_dataset import UploadedDataset
from app.services.dataset_store import TenantDatasetStore


def _create_workspace(client, suffix):
    response = client.post('/api/v1/auth/register-admin', json={
        'full_name': 'Journey Analyst', 'phone_number': '+1555111222',
        'email': f'journey_{suffix}@example.com', 'username': f'journey_{suffix}',
        'password': 'Password123!', 'confirm_password': 'Password123!',
        'company_name': f'Journey {suffix}', 'industry': 'Retail/E-commerce',
    })
    assert response.status_code == 201, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def _frame():
    return pd.DataFrame([
        {'date': f'2026-01-{day + 1:02d}', 'region': region,
         'revenue': (100 + 5 * day + (20 if day >= 12 else 0)) if region == 'North' else 80 + 2 * day,
         'cost': (40 if region == 'North' else 30) + day,
         'note': None if day == 0 and region == 'North' else 'verified'}
        for day in range(24) for region in ['North', 'South']
    ])


def _upload(client, headers, frame, extension):
    if extension == 'xlsx':
        buffer = io.BytesIO()
        frame.to_excel(buffer, index=False)
        content, media_type = buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif extension == 'json':
        content, media_type = frame.to_json(orient='records').encode(), 'application/json'
    else:
        content, media_type = frame.to_csv(index=False).encode(), 'text/csv'
    response = client.post('/api/v1/data/upload', headers=headers,
                           files={'file': (f'journey.{extension}', content, media_type)})
    assert response.status_code == 200, response.text
    assert response.json()['status'] in ['success', 'partial_success'], response.text


def _note(client, headers, kind, title, content):
    response = client.post('/api/v1/analysis/records', headers=headers,
                           json={'kind': kind, 'title': title, 'content': content})
    assert response.status_code == 201, response.text
    return response.json()


def _run(client, headers, method, parameters):
    response = client.post('/api/v1/analysis/run', headers=headers,
                           json={'method': method, 'title': f'{method} evidence', 'parameters': parameters})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize('extension', ['csv', 'xlsx', 'json'])
def test_full_analyst_journey_preserves_evidence_and_rejects_stale_formulas(client, db_session, extension):
    TenantDatasetStore.clear_all()
    headers = _create_workspace(client, extension)
    brief = _note(client, headers, 'brief', 'Regional investment decision', {
        'question': 'Which region accounts for the change in revenue?',
        'decision': 'Assign investigation owners before changing investment.',
        'target': 'Preserve profit while understanding the regional change.',
        'stakeholders': 'Finance and regional managers',
    })
    frame = _frame()
    _upload(client, headers, frame, extension)
    response = client.get('/api/v1/analysis/profile', headers=headers)
    assert response.status_code == 200, response.text
    profile = response.json()
    revision = profile['revision']
    assert profile['rows'] == 48 and profile['duplicates'] == 0
    assert profile['missing_cells'] == 1
    assert {'revenue', 'cost'} <= set(profile['numeric_columns'])
    revenue = next(column for column in profile['columns'] if column['name'] == 'revenue')
    assert revenue['statistics']['mean'] == pytest.approx(frame.revenue.mean())

    profit = float((frame.revenue - frame.cost).sum())
    profit_rule = _note(client, headers, 'metric_rule', 'Profit target', {
        'expression': 'revenue - cost', 'target': profit - 1,
        'aggregation': 'sum', 'direction': 'at_least',
    })
    cost_rule = _note(client, headers, 'metric_rule', 'Mean cost ceiling', {
        'expression': 'cost', 'target': float(frame.cost.mean() - 1),
        'aggregation': 'mean', 'direction': 'at_most',
    })
    metrics = client.get('/api/v1/analysis/metrics', headers=headers).json()
    profit_metric = next(row for row in metrics if row['id'] == profit_rule['id'])
    cost_metric = next(row for row in metrics if row['id'] == cost_rule['id'])
    assert profit_metric['value'] == pytest.approx(profit)
    assert profit_metric['target_met'] is True and profit_metric['valid_rows'] == 48
    assert cost_metric['value'] == pytest.approx(frame.cost.mean())
    assert cost_metric['target_met'] is False

    aggregate = _run(client, headers, 'aggregate', {'metric': 'revenue', 'dimensions': ['region']})
    totals = {row['region']: row['value'] for row in aggregate['content']['result']['rows']}
    assert totals == frame.groupby('region').revenue.sum().to_dict()
    formula = _run(client, headers, 'formula', {'expression': '(revenue - cost) / revenue * 100'})
    assert formula['content']['result']['mean'] == pytest.approx(((frame.revenue - frame.cost) / frame.revenue * 100).mean())
    compare = _run(client, headers, 'compare', {'metric': 'revenue', 'dimension': 'region', 'baseline': 'South', 'comparison': 'North'})
    comparison = compare['content']['result']
    assert comparison['baseline_n'] == comparison['comparison_n'] == 24
    assert comparison['mean_difference'] == pytest.approx(frame[frame.region == 'North'].revenue.mean() - frame[frame.region == 'South'].revenue.mean())
    assert comparison['p_value'] < 0.01
    assert comparison['confidence_interval_95'][0] > 0

    investigate = _run(client, headers, 'investigate', {
        'metric': 'revenue', 'date_column': 'date', 'dimension': 'region', 'split_date': '2026-01-13',
    })
    contributions = investigate['content']['result']
    assert contributions['baseline_observed_days'] == contributions['comparison_observed_days'] == 12
    assert contributions['net_change'] == pytest.approx(104)
    assert sum(row['change'] for row in contributions['rows']) == pytest.approx(104)
    assert sum(row['share_of_net_change_pct'] for row in contributions['rows']) == pytest.approx(100)

    trend = _run(client, headers, 'trend', {'metric': 'revenue', 'date_column': 'date', 'horizon': 7})
    forecast = trend['content']['result']
    assert len(forecast['history']) == 24 and len(forecast['forecast']) == 7
    assert forecast['forecast'][0]['date'].startswith('2026-01-25')
    assert forecast['validation_observations'] == 6
    assert forecast['backtest_mae'][forecast['method']] == min(forecast['backtest_mae'].values())
    assert all(point['low'] <= point['value'] <= point['high'] for point in forecast['forecast'])
    # Saving evidence must include finite JSON and the exact source revision.
    runs = [aggregate, formula, compare, investigate, trend]
    for run in runs:
        assert run['dataset_revision'] == revision and run['stale'] is False
        json.dumps(run['content'], allow_nan=False)

    unsafe_text = '<img src=x onerror="alert(1)"> & finance'
    finding = _note(client, headers, 'finding', '<script>not executable</script>', {
        'evidence_id': investigate['id'], 'hypothesis': unsafe_text,
        'owner': 'Regional manager', 'status': 'Proposed',
        'validation': 'Review collection changes and the largest revenue contributors.',
    })
    for status, outcome in [('In progress', 'Validated source coverage.'), ('Completed', 'Regional review completed; follow-up experiment proposed.')]:
        response = client.post(f"/api/v1/analysis/records/{finding['id']}/progress", headers=headers,
                               json={'status': status, 'outcome': outcome})
        assert response.status_code == 200, response.text
        event = response.json()
        assert event['kind'] == 'action_update'
        assert event['content'] == {'parent_id': finding['id'], 'status': status, 'outcome': outcome}
        assert event['dataset_revision'] == revision
    comment = _note(client, headers, 'comment', 'Finance review', {'parent_id': finding['id'], 'text': unsafe_text})
    for record in [finding, comment]:
        export = client.get(f"/api/v1/analysis/records/{record['id']}/download", headers=headers)
        assert export.status_code == 200 and export.headers['content-type'].startswith('text/html')
        assert 'attachment;' in export.headers['content-disposition']
        assert unsafe_text not in export.text and escape(unsafe_text) in export.text
        assert '<script>not executable</script>' not in export.text
        assert 'Dataset revision matched at export.' in export.text

    _note(client, headers, 'monitor', 'Data quality guardrails', {'max_age_hours': 24, 'max_missing_percent': 0})
    stored = db_session.query(UploadedDataset).one()
    stored.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
    db_session.commit()
    monitor = client.get('/api/v1/analysis/monitor', headers=headers)
    assert monitor.status_code == 200, monitor.text
    checks = {check['name']: check for check in monitor.json()['checks']}
    assert checks['Upload freshness']['alert'] is True
    assert checks['Upload freshness']['value'] == pytest.approx(48, abs=0.02)
    assert checks['Missing cells']['value'] == pytest.approx(round(100 / frame.size, 2))
    assert checks['Missing cells']['alert'] is True

    before = db_session.query(AnalysisRecord).count()
    for _ in range(2):
        for path in ['profile', 'metrics', 'records', 'monitor', f"records/{investigate['id']}/download"]:
            assert client.get(f'/api/v1/analysis/{path}', headers=headers).status_code == 200
    assert db_session.query(AnalysisRecord).count() == before, 'Read endpoints must not create evidence records.'

    _upload(client, headers, pd.DataFrame({'product': ['Widget', 'Gadget'], 'units': [5, 9]}), 'json')
    current = client.get('/api/v1/analysis/profile', headers=headers).json()
    assert current['rows'] == 2 and current['revision'] != revision
    saved = {record['id']: record for record in client.get('/api/v1/analysis/records', headers=headers).json()}
    assert saved[brief['id']]['stale'] is False
    assert all(saved[run['id']]['stale'] is True for run in runs)
    assert saved[finding['id']]['stale'] is True
    assert saved[investigate['id']]['content']['result'] == contributions, 'Historical evidence must retain its original results.'
    export = client.get(f"/api/v1/analysis/records/{investigate['id']}/download", headers=headers)
    assert 'Historical result: the active dataset has changed.' in export.text
    before = db_session.query(AnalysisRecord).count()
    invalid_metrics = client.get('/api/v1/analysis/metrics', headers=headers).json()
    assert len(invalid_metrics) == 2
    assert all(row['value'] is None and row['target_met'] is None and 'current dataset' in row['error'] for row in invalid_metrics)
    invalid_run = client.post('/api/v1/analysis/run', headers=headers,
                              json={'method': 'formula', 'parameters': {'expression': 'revenue - cost'}})
    assert invalid_run.status_code == 422 and 'Unknown column' in invalid_run.text
    assert db_session.query(AnalysisRecord).count() == before
