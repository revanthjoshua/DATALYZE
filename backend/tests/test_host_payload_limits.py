import asyncio
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import HTTPException

from app.api.v1 import data_routes
from app.core.config import settings
from app.middleware.auth_middleware import get_current_user
from app.services.data_ingestion_service import DataIngestionService
from app.services.payload_limits import check_response_size


class DatasetQuery:
    def __init__(self, dataset):
        self.dataset = dataset

    def query(self, *_):
        return self

    def filter(self, *_):
        return self

    def order_by(self, *_):
        return self

    def first(self):
        return self.dataset


def test_capabilities_are_authenticated_and_match_effective_host_limits(monkeypatch):
    import inspect
    monkeypatch.setattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 4_000_000)
    monkeypatch.setattr(settings, 'MAX_REQUEST_SIZE_BYTES', 4_250_000)
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', 4_000_000)
    dependency = inspect.signature(data_routes.data_capabilities).parameters['current_user'].default
    assert dependency.dependency is get_current_user
    assert data_routes.data_capabilities(SimpleNamespace(company_id=1)) == {
        'max_upload_bytes': 4_000_000, 'max_request_bytes': 4_250_000,
        'max_response_bytes': 4_000_000, 'editor_max_rows': 10000,
    }


def test_oversized_upload_stops_before_parsing_and_reads_only_the_limit_plus_one(monkeypatch):
    monkeypatch.setattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 20)
    reads = []

    class Upload:
        filename = 'source.csv'

        async def seek(self, _):
            pass

        async def read(self, size):
            reads.append(size)
            return b'x' * size

    service = DataIngestionService(1)
    monkeypatch.setattr(service, 'parse_raw_content', lambda *_: pytest.fail('Oversized content must not be parsed'))
    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service.read_uploaded_file(Upload()))
    assert rejected.value.status_code == 413
    assert 'active dataset is unchanged' in rejected.value.detail
    assert reads == [21]


def test_editor_is_complete_or_rejected_without_truncating_the_dataset(monkeypatch):
    frame = pd.DataFrame({'record_id': ['001', '002'], 'text': ['₹' * 20, 'final row'], '_helper': [0, 0]})
    before = frame.copy(deep=True)
    dataset = SimpleNamespace(id=1, file_hash='original', filename='source.csv')
    db = DatasetQuery(dataset)
    user = SimpleNamespace(company_id=9)
    monkeypatch.setattr(data_routes, '_ensure_dataset_loaded', lambda *_: frame)
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', 100)
    with pytest.raises(HTTPException) as rejected:
        data_routes.get_editor_snapshot(user, db)
    assert rejected.value.status_code == 413
    assert 'stored dataset is unchanged' in rejected.value.detail
    pd.testing.assert_frame_equal(frame, before)
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', None)
    result = data_routes.get_editor_snapshot(user, db)
    assert result['records'][-1] == {'record_id': '002', 'text': 'final row'}
    assert result['total_rows'] == 2
    assert result['revision'] == '1:original'


def test_csv_export_limit_keeps_complete_source_available_on_an_unrestricted_host(monkeypatch):
    frame = pd.DataFrame({'text': ['₹' * 20, 'final row']})
    before = frame.copy(deep=True)
    monkeypatch.setattr(data_routes, '_ensure_dataset_loaded', lambda *_: frame)
    db = DatasetQuery(SimpleNamespace(filename='source.csv'))
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', 30)
    with pytest.raises(HTTPException) as rejected:
        data_routes.download_active_dataset(1, db)
    assert rejected.value.status_code == 413
    pd.testing.assert_frame_equal(frame, before)
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', None)
    assert data_routes.download_active_dataset(1, db).body.decode() == frame.to_csv(index=False)


def test_response_limit_counts_utf8_and_includes_the_boundary(monkeypatch):
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', 6)
    check_response_size('₹₹', 'Export')
    with pytest.raises(HTTPException) as rejected:
        check_response_size('₹₹x', 'Export')
    assert rejected.value.status_code == 413


def account(client, name):
    response = client.post('/api/v1/auth/register-admin', json={
        'full_name': name, 'phone_number': '+1555111222', 'email': f'{name}@example.com', 'username': name,
        'password': 'Password123!', 'confirm_password': 'Password123!', 'company_name': name, 'industry': 'Retail/E-commerce'})
    assert response.status_code == 201, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_capabilities_require_an_authenticated_session(client):
    assert client.get('/api/v1/data/capabilities').status_code == 401
    headers = account(client, 'payload_reader')
    response = client.get('/api/v1/data/capabilities', headers=headers)
    assert response.status_code == 200
    assert response.json()['max_upload_bytes'] == settings.MAX_UPLOAD_SIZE_BYTES


def test_upload_limits_cover_active_library_and_join_without_replacing_source(client, monkeypatch):
    headers = account(client, 'payload_uploads')
    source = b'code,revenue\nA,10\nB,20\n'
    uploaded = client.post('/api/v1/data/upload', headers=headers, files={'file': ('source.csv', source, 'text/csv')})
    assert uploaded.status_code == 200, uploaded.text
    before = client.get('/api/v1/data/dataset/editor', headers=headers).json()
    revision = client.get('/api/v1/analysis/profile', headers=headers).json()['revision']
    monkeypatch.setattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 20)
    for path, fields in [
        ('/data/upload', {}), ('/datasets/upload', {'name': 'Too large'}),
        ('/analysis/join', {'left_key': 'code', 'right_key': 'code', 'dataset_revision': revision, 'apply': 'true'}),
    ]:
        response = client.post('/api/v1' + path, headers=headers, data=fields,
                               files={'file': ('source.csv', source, 'text/csv')})
        assert response.status_code == 413, response.text
        assert 'active dataset is unchanged' in response.json()['detail']
    assert client.get('/api/v1/analysis/profile', headers=headers).json()['revision'] == revision
    assert client.get('/api/v1/data/dataset/editor', headers=headers).json() == before
    assert client.get('/api/v1/datasets', headers=headers).json() == []


def test_library_backup_and_evidence_exports_reject_without_changing_saved_records(client, db_session, monkeypatch):
    from app.models.analysis_record import AnalysisRecord
    headers = account(client, 'payload_exports')
    source = b'code,revenue\nA,10\nB,20\n'
    saved = client.post('/api/v1/datasets/upload', headers=headers, data={'name': 'Library source'},
                        files={'file': ('source.csv', source, 'text/csv')})
    assert saved.status_code == 201, saved.text
    for text in (source, b'code,revenue\nC,30\n'):
        uploaded = client.post('/api/v1/data/upload', headers=headers, files={'file': ('source.csv', text, 'text/csv')})
        assert uploaded.status_code == 200, uploaded.text
    brief = client.post('/api/v1/analysis/records', headers=headers,
                        json={'kind': 'brief', 'title': 'Decision', 'content': {'question': 'Where should we focus?'}})
    assert brief.status_code == 201, brief.text
    backup = next(row for row in client.get('/api/v1/analysis/records', headers=headers).json() if row['kind'] == 'backup')
    ids = [saved.json()['id'], backup['id'], brief.json()['id']]
    before = {row.id: row.content for row in db_session.query(AnalysisRecord).filter(AnalysisRecord.id.in_(ids))}
    paths = [f"/api/v1/datasets/{ids[0]}/download", f"/api/v1/analysis/records/{ids[1]}/download", f"/api/v1/analysis/records/{ids[2]}/download"]
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', 10)
    for path in paths:
        response = client.get(path, headers=headers)
        assert response.status_code == 413, response.text
        assert 'stored dataset is unchanged' in response.json()['detail']
    db_session.expire_all()
    assert {row.id: row.content for row in db_session.query(AnalysisRecord).filter(AnalysisRecord.id.in_(ids))} == before
    monkeypatch.setattr(settings, 'MAX_RESPONSE_SIZE_BYTES', None)
    for path in paths:
        assert client.get(path, headers=headers).status_code == 200
