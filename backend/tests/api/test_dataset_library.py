import io

import pandas as pd

from app.models.analysis_record import AnalysisRecord
from app.models.user import User
from app.services.dataset_library_service import DatasetLibraryService
from app.services.dataset_store import TenantDatasetStore


def account(client, name):
    response = client.post('/api/v1/auth/register-admin', json={
        'full_name': name, 'phone_number': '+1555111222', 'email': f'{name}@example.com', 'username': name,
        'password': 'Password123!', 'confirm_password': 'Password123!', 'company_name': name, 'industry': 'Retail/E-commerce'})
    assert response.status_code == 201, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def upload(client, headers, text, saved=False, name='Saved source'):
    response = client.post('/api/v1/datasets/upload' if saved else '/api/v1/data/upload', headers=headers,
                           data={'name': name} if saved else {},
                           files={'file': ('source.csv', io.BytesIO(text.encode()), 'text/csv')})
    assert response.status_code == (201 if saved else 200), response.text
    return response.json()


def revision(client, headers):
    response = client.get('/api/v1/analysis/profile', headers=headers)
    assert response.status_code == 200, response.text
    return response.json()['revision']


def test_library_upload_activate_switch_preserves_immutable_sources_and_previous_backup(client):
    TenantDatasetStore.clear_all()
    headers = account(client, 'library_switch')
    saved = upload(client, headers, 'code,region,sales\n001,NA,10\n002,South,20\n', saved=True, name='January')
    dataset_id = saved['id']
    assert 'snapshot' not in saved
    assert client.get('/api/v1/analysis/profile', headers=headers).status_code == 404
    activated = client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': ''})
    assert activated.status_code == 200, activated.text
    old_revision = revision(client, headers)
    saved_active = client.post('/api/v1/datasets/save', headers=headers, json={'name': 'January normalized', 'revision': old_revision})
    assert saved_active.status_code == 201, saved_active.text
    upload(client, headers, 'code,region,sales\n003,West,90\n')
    current_revision = revision(client, headers)
    stale = client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': old_revision})
    assert stale.status_code == 409
    assert revision(client, headers) == current_revision
    preview = client.get(f'/api/v1/datasets/{dataset_id}/preview', headers=headers).json()
    assert preview['preview'][0] == {'code': '001', 'region': 'NA', 'sales': '10'}
    assert 'snapshot' not in preview
    restored = client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': current_revision})
    assert restored.status_code == 200, restored.text
    assert client.get('/api/v1/analysis/profile', headers=headers).json()['rows'] == 2
    history = client.get('/api/v1/analysis/records', headers=headers).json()
    assert not any(row['kind'] in ('saved_dataset', 'dataset_state') for row in history)
    assert any(row['kind'] == 'backup' and row['content']['rows'] == 1 for row in history)
    assert client.delete('/api/v1/data/dataset', headers=headers).status_code == 200
    assert len(client.get('/api/v1/datasets', headers=headers).json()) == 2
    assert client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': ''}).status_code == 200


def test_library_archive_restore_optimistic_versions_and_viewer_scope(client, db_session):
    headers, other = account(client, 'library_owner'), account(client, 'library_other')
    saved = upload(client, headers, 'key,label\nA,North\nB,South\n', saved=True)
    dataset_id = saved['id']
    for suffix in ('preview', 'download'):
        assert client.get(f'/api/v1/datasets/{dataset_id}/{suffix}', headers=other).status_code == 404
    for suffix, payload in [('activate', {'revision': ''}), ('state', {'archived': True, 'version': 0}),
                            ('join', {'revision': '', 'left_key': 'key', 'right_key': 'key'})]:
        assert client.post(f'/api/v1/datasets/{dataset_id}/{suffix}', headers=other, json=payload).status_code == 404
    assert client.get('/api/v1/datasets', headers=other).json() == []
    archived = client.post(f'/api/v1/datasets/{dataset_id}/state', headers=headers, json={'archived': True, 'version': 0})
    assert archived.status_code == 200, archived.text
    assert archived.json()['archived'] is True
    assert client.get('/api/v1/datasets', headers=headers).json() == []
    assert client.get('/api/v1/datasets?include_archived=true', headers=headers).json()[0]['archived'] is True
    assert client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': ''}).status_code == 409
    assert client.post(f'/api/v1/datasets/{dataset_id}/state', headers=headers, json={'archived': False, 'version': 0}).status_code == 409
    restored = client.post(f'/api/v1/datasets/{dataset_id}/state', headers=headers,
                           json={'archived': False, 'version': archived.json()['version']})
    assert restored.status_code == 200
    user = db_session.query(User).filter_by(username='library_owner').first()
    user.role = 'viewer'
    db_session.commit()
    assert client.get(f'/api/v1/datasets/{dataset_id}/preview', headers=headers).status_code == 200
    assert client.get(f'/api/v1/datasets/{dataset_id}/download', headers=headers).status_code == 200
    assert client.post(f'/api/v1/datasets/{dataset_id}/activate', headers=headers, json={'revision': ''}).status_code == 403
    assert client.post('/api/v1/datasets/save', headers=headers, json={'name': 'Denied', 'revision': 'anything'}).status_code == 403
    assert client.post(f'/api/v1/datasets/{dataset_id}/state', headers=headers,
                       json={'archived': True, 'version': restored.json()['version']}).status_code == 403


def test_saved_dataset_composite_join_preview_apply_and_stale_rejection(client):
    TenantDatasetStore.clear_all()
    headers = account(client, 'library_join')
    upload(client, headers, 'code,region,sales\n001,N,10\n001,N,20\n001,S,30\n002,S,40\n')
    rev = revision(client, headers)
    lookup = upload(client, headers, 'code,region,label\n001,N,North branch\n001,S,South branch\n002,S,Other branch\n', saved=True)
    payload = {'revision': rev, 'left_key': ['code', 'region'], 'right_key': ['code', 'region'], 'how': 'left', 'cardinality': 'many_to_one'}
    preview = client.post(f"/api/v1/datasets/{lookup['id']}/join", headers=headers, json=payload)
    assert preview.status_code == 200, preview.text
    assert preview.json()['rows_after'] == 4
    assert preview.json()['matched_rows'] == 4
    assert preview.json()['preview'][0]['label'] == 'North branch'
    assert revision(client, headers) == rev
    applied = client.post(f"/api/v1/datasets/{lookup['id']}/join", headers=headers, json={**payload, 'apply': True})
    assert applied.status_code == 200, applied.text
    assert applied.json()['applied'] is True
    assert client.post(f"/api/v1/datasets/{lookup['id']}/join", headers=headers, json={**payload, 'apply': True}).status_code == 409
    lookup_after = client.get(f"/api/v1/datasets/{lookup['id']}/preview", headers=headers).json()
    assert lookup_after['rows'] == 3
    assert lookup_after['checksum'] == lookup['checksum']


def test_library_snapshot_types_integrity_limits_and_safe_download(client, db_session, monkeypatch):
    headers = account(client, 'library_types')
    user = db_session.query(User).filter_by(username='library_types').first()
    service = DatasetLibraryService(db_session, user)
    frame = pd.DataFrame({'code': ['001', '002'], 'count': pd.Series([1, None], dtype='Int64'),
                          'date': pd.to_datetime(['2026-01-01', '2026-01-02'], utc=True),
                          'text': ['=SUM(1,2)', 'NA']})
    saved = service.save(frame, 'Types', '', 'typed.csv')
    restored = service.frame(service.get(saved['id']))
    assert restored['code'].tolist() == ['001', '002']
    assert restored['count'].isna().tolist() == [False, True]
    assert restored['date'].dt.year.tolist() == [2026, 2026]
    download = client.get(f"/api/v1/datasets/{saved['id']}/download", headers=headers)
    assert "'=SUM(1,2)" in download.text
    assert service.frame(service.get(saved['id']))['text'].iloc[0] == '=SUM(1,2)'
    monkeypatch.setattr('app.services.dataset_library_service.MAX_SNAPSHOT_BYTES', 1)
    limited = client.post('/api/v1/datasets/upload', headers=headers, data={'name': 'Too large'},
                          files={'file': ('small.csv', io.BytesIO(b'code,value\nA,10\n'), 'text/csv')})
    assert limited.status_code == 413
    assert len(client.get('/api/v1/datasets', headers=headers).json()) == 1
    row = db_session.query(AnalysisRecord).filter_by(id=saved['id']).first()
    row.content = {**row.content, 'snapshot': row.content['snapshot'] + ' '}
    db_session.commit()
    assert client.get(f"/api/v1/datasets/{saved['id']}/preview", headers=headers).status_code == 409
    assert client.post(f"/api/v1/datasets/{saved['id']}/activate", headers=headers, json={'revision': ''}).status_code == 409
    assert client.get('/api/v1/analysis/profile', headers=headers).status_code == 404



def test_saved_dataset_download_escapes_headers_without_changing_snapshot(client, db_session):
    import csv
    headers = account(client, 'library_header_safety')
    user = db_session.query(User).filter_by(username='library_header_safety').one()
    service = DatasetLibraryService(db_session, user)
    columns = ['=1+1', '+2+2', '-3+3', '@SUM(A1)', '  =4+4', 'ordinary']
    frame = pd.DataFrame([['=10+10', 'text', 3, 4, 5, 'plain']], columns=columns)
    saved = service.save(frame, 'Unsafe headers', '', 'headers.csv')
    download = client.get(f"/api/v1/datasets/{saved['id']}/download", headers=headers)
    assert download.status_code == 200
    rows = list(csv.reader(io.StringIO(download.text.lstrip('\ufeff'))))
    assert rows[0] == ["'" + name for name in columns[:-1]] + ['ordinary']
    assert rows[1][0] == "'=10+10"
    original = service.frame(service.get(saved['id']))
    assert original.columns.tolist() == columns
    assert original.iloc[0, 0] == '=10+10'



def test_dated_active_snapshot_round_trip_keeps_public_columns(client, db_session):
    TenantDatasetStore.clear_all()
    headers = account(client, 'library_dated_round_trip')
    upload(client, headers, 'date,region,sales\n2026-01-01,North,10\n2026-01-02,South,20\n2026-01-03,North,30\n')
    user = db_session.query(User).filter_by(username='library_dated_round_trip').one()
    service = DatasetLibraryService(db_session, user)
    expected = ['date', 'region', 'sales']
    for index in range(2):
        current_revision = revision(client, headers)
        _, cached_frame = service.source(current_revision)
        assert '_parsed_date' in cached_frame.columns
        saved = client.post('/api/v1/datasets/save', headers=headers,
                            json={'name': f'Dated round trip {index}', 'revision': current_revision})
        assert saved.status_code == 201, saved.text
        saved = saved.json()
        assert saved['columns'] == expected
        preview = client.get(f"/api/v1/datasets/{saved['id']}/preview", headers=headers).json()
        assert list(preview['preview'][0]) == expected
        activated = client.post(f"/api/v1/datasets/{saved['id']}/activate", headers=headers,
                                json={'revision': current_revision})
        assert activated.status_code == 200, activated.text
        profile = client.get('/api/v1/analysis/profile', headers=headers).json()
        assert [column['name'] for column in profile['columns']] == expected
        assert profile['rows'] == 3
        _, restored = service.source(profile['revision'])
        assert restored['sales'].tolist() == [10, 20, 30]


def test_legacy_dated_snapshot_filters_helpers_when_activated_or_joined(client, db_session):
    TenantDatasetStore.clear_all()
    headers = account(client, 'library_legacy_helpers')
    upload(client, headers, 'date,region,sales\n2026-01-01,North,10\n2026-01-02,South,20\n2026-01-03,West,30\n')
    user = db_session.query(User).filter_by(username='library_legacy_helpers').one()
    service = DatasetLibraryService(db_session, user)
    current_revision = revision(client, headers)
    _, cached_frame = service.source(current_revision)
    assert '_parsed_date' in cached_frame.columns
    # Reproduce an immutable snapshot created before helper filtering was fixed.
    legacy = service.save(cached_frame, 'Legacy active snapshot', '', 'legacy.csv', current_revision)
    assert '_parsed_date' in legacy['columns']
    original_snapshot = service.get(legacy['id']).content['snapshot']
    for _ in range(2):
        activated = client.post(f"/api/v1/datasets/{legacy['id']}/activate", headers=headers,
                                json={'revision': revision(client, headers)})
        assert activated.status_code == 200, activated.text
        profile = client.get('/api/v1/analysis/profile', headers=headers).json()
        assert [column['name'] for column in profile['columns']] == ['date', 'region', 'sales']
    preview = client.post(f"/api/v1/datasets/{legacy['id']}/join", headers=headers, json={
        'revision': revision(client, headers), 'left_key': 'region', 'right_key': 'region',
        'how': 'left', 'cardinality': 'one_to_one',
    })
    assert preview.status_code == 200, preview.text
    assert not any(column.startswith('_') or column == 'parsed_date' for column in preview.json()['columns'])
    assert service.get(legacy['id']).content['snapshot'] == original_snapshot
    assert service.get(legacy['id']).content['metadata']['checksum'] == legacy['checksum']


def test_raw_library_upload_preserves_user_underscore_columns(client):
    TenantDatasetStore.clear_all()
    headers = account(client, 'library_raw_underscore')
    saved = upload(client, headers, '_customer,_parsed_date,sales\nA,first source note,10\nB,second source note,20\n', saved=True)
    assert saved['source_revision'] is None
    assert saved['columns'] == ['_customer', '_parsed_date', 'sales']
    activated = client.post(f"/api/v1/datasets/{saved['id']}/activate", headers=headers, json={'revision': ''})
    assert activated.status_code == 200, activated.text
    profile = client.get('/api/v1/analysis/profile', headers=headers).json()
    assert [column['name'] for column in profile['columns']] == ['customer', 'parsed_date', 'sales']
    preview = client.get(f"/api/v1/datasets/{saved['id']}/preview", headers=headers).json()
    assert preview['preview'][0] == {'_customer': 'A', '_parsed_date': 'first source note', 'sales': '10'}
    assert preview['checksum'] == saved['checksum']
