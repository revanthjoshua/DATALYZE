import io
from app.services.dataset_store import TenantDatasetStore


def register(client, name):
    response = client.post('/api/v1/auth/register-admin', json={
        'full_name': name, 'phone_number': '+1555111222',
        'email': f'{name}@example.com', 'username': name,
        'password': 'Password123!', 'confirm_password': 'Password123!',
        'company_name': name, 'industry': 'Retail/E-commerce',
    })
    assert response.status_code == 201, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def test_complete_editor_roundtrip_and_stale_save(client):
    TenantDatasetStore.clear_all()
    headers = register(client, 'editor_admin')
    csv = 'record_id,revenue,region\n' + ''.join(
        f'ID-{i:04d},{i + 0.125},North\n' for i in range(250)
    )
    response = client.post('/api/v1/data/upload', headers=headers,
        files={'file': ('editor.csv', io.BytesIO(csv.encode()), 'text/csv')})
    assert response.status_code == 200, response.text
    snapshot = client.get('/api/v1/data/dataset/editor', headers=headers)
    assert snapshot.status_code == 200, snapshot.text
    data = snapshot.json()
    assert len(data['records']) == 250
    assert data['records'][-1]['record_id'] == 'ID-0249'
    data['records'][0]['revenue'] = 987.125
    payload = {'records': data['records'], 'revision': data['revision'], 'filename': 'editor.csv'}
    saved = client.put('/api/v1/data/dataset', headers=headers, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()['processed_rows'] == 250
    reread = client.get('/api/v1/data/dataset/editor', headers=headers).json()
    assert len(reread['records']) == 250
    assert reread['records'][0]['revenue'] == 987.125
    assert reread['records'][-1]['record_id'] == 'ID-0249'
    backups=client.get('/api/v1/analysis/records',headers=headers).json()
    backup=next(row for row in backups if row['kind']=='backup')
    contents=client.get(f"/api/v1/analysis/records/{backup['id']}/download",headers=headers).text
    assert 'ID-0249' in contents and '987.125' not in contents
    stale = client.put('/api/v1/data/dataset', headers=headers, json=payload)
    assert stale.status_code == 409
    unversioned = client.put('/api/v1/data/dataset', headers=headers, json={'records': data['records'][:100]})
    assert unversioned.status_code == 428
    other_headers = register(client, 'editor_other')
    assert client.get('/api/v1/data/dataset/editor', headers=other_headers).status_code == 404
