import pytest

from app.services.dataset_store import TenantDatasetStore


@pytest.fixture
def raw_headers(client):
    TenantDatasetStore.clear_all()
    response = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Raw ingestion", "phone_number": "+1555111222",
        "email": "raw-ingestion@example.com", "username": "raw_ingestion",
        "password": "Password123!", "confirm_password": "Password123!",
        "company_name": "Raw ingestion", "industry": "Retail/E-commerce",
    })
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.mark.parametrize("payload", [
    {},
    {"records": []},
    {"data": []},
    {"records": None},
    {"data": "not a record"},
    {"records": 42},
    {"records": {}},
    {"records": [1, 2]},
    {"records": [{"amount": 99}, "not a record"]},
    {"data": [{"amount": 99}, None]},
    {"records": [{}]},
    {"records": [], "data": [{"amount": 99}]},
])
def test_invalid_raw_records_leave_active_dataset_unchanged(client, raw_headers, payload):
    seed = client.post("/api/v1/data/ingest-raw", headers=raw_headers, json={
        "records": [{"item_id": "A", "amount": 10}, {"item_id": "B", "amount": 20}],
    })
    assert seed.status_code == 200, seed.text
    before = client.get("/api/v1/data/dataset/editor", headers=raw_headers)
    assert before.status_code == 200, before.text

    rejected = client.post("/api/v1/data/ingest-raw", headers=raw_headers, json=payload)
    assert rejected.status_code == 400, rejected.text
    assert "record" in rejected.json()["detail"]
    after = client.get("/api/v1/data/dataset/editor", headers=raw_headers)
    assert after.status_code == 200, after.text
    assert after.json() == before.json()


@pytest.mark.parametrize("payload, expected", [
    ({"item_id": "A", "amount": 10}, [10]),
    ({"records": {"item_id": "A", "amount": 10}}, [10]),
    ({"data": {"item_id": "A", "amount": 10}}, [10]),
    ({"records": [{"item_id": "A", "amount": 10}, {"item_id": "B", "amount": 20}]}, [10, 20]),
    ({"data": [{"item_id": "A", "amount": 10}, {"item_id": "B", "amount": 20}]}, [10, 20]),
])
def test_raw_ingestion_preserves_supported_record_shapes(client, raw_headers, payload, expected):
    response = client.post("/api/v1/data/ingest-raw", headers=raw_headers, json=payload)
    assert response.status_code == 200, response.text
    editor = client.get("/api/v1/data/dataset/editor", headers=raw_headers)
    assert editor.status_code == 200, editor.text
    assert [row["amount"] for row in editor.json()["records"]] == expected
