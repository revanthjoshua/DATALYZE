import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.models.company import Company
from app.models.dataset_blob import DatasetStorageBlob
from app.services.storage_service import (
    DatabaseStorageBackend,
    LocalStorageBackend,
    S3StorageBackend,
    StorageService,
)


def test_local_storage_cannot_read_or_delete_other_tenant(tmp_path):
    backend = LocalStorageBackend(str(tmp_path / "storage"))
    own_key = backend.save(1, "data.csv", b"first")
    other_key = backend.save(2, "data.csv", b"second")
    outside = tmp_path / "unrelated.csv"
    outside.write_bytes(b"outside")
    for key in (other_key, str(outside), "../2/datasets/data.csv", "..\\2\\datasets\\data.csv"):
        with pytest.raises(ValueError):
            backend.get(1, key)
        with pytest.raises(ValueError):
            backend.delete(1, key)
    assert backend.get(1, own_key) == b"first"
    assert backend.get(2, other_key) == b"second"
    assert outside.read_bytes() == b"outside"


@pytest.mark.parametrize("filename", ["../escape.csv", "..\\escape.csv", "C:\\escape.csv", "data.csv:stream", "NUL.csv", "data\n.csv"])
def test_storage_rejects_path_filenames(tmp_path, filename):
    with pytest.raises(ValueError):
        LocalStorageBackend(str(tmp_path)).save(1, filename, b"data")


def test_local_purge_errors_are_not_reported_as_success(tmp_path, monkeypatch):
    backend = LocalStorageBackend(str(tmp_path / "storage"))
    backend.save(1, "first.csv", b"first")
    other_key = backend.save(2, "second.csv", b"second")
    monkeypatch.setattr("app.services.storage_service.shutil.rmtree", Mock(side_effect=PermissionError("locked")))
    with pytest.raises(PermissionError):
        backend.delete_all(1)
    assert backend.get(2, other_key) == b"second"


def test_database_keys_are_exact_and_obey_outer_transaction(db_session):
    db_session.add_all([Company(id=1, name="A"), Company(id=2, name="B")])
    db_session.commit()
    backend = DatabaseStorageBackend()
    first_key = backend.save(1, "same.csv", b"first", db=db_session)
    second_key = backend.save(2, "same.csv", b"second", db=db_session)
    with pytest.raises(ValueError):
        backend.get(1, second_key, db=db_session)
    with pytest.raises(ValueError):
        backend.delete(1, second_key, db=db_session)
    assert backend.get(1, first_key, db=db_session) == b"first"
    assert backend.get(2, second_key, db=db_session) == b"second"
    db_session.info["dataset_transaction"] = True
    try:
        backend.save(1, "pending.csv", b"pending", db=db_session)
        db_session.rollback()
        assert db_session.query(DatasetStorageBlob).filter_by(filename="pending.csv").count() == 0
    finally:
        db_session.info.pop("dataset_transaction", None)


def s3_backend():
    backend = S3StorageBackend()
    backend.bucket = "test-bucket"
    backend._client = Mock()
    backend._client.get_object.return_value = {"Body": io.BytesIO(b"dataset")}
    return backend


@pytest.mark.parametrize("key", [
    "s3://test-bucket/tenants/2/datasets/file.csv",
    "s3://other-bucket/tenants/1/datasets/file.csv",
    "tenants/1/datasets/../../2/file.csv",
    "tenants/10/datasets/file.csv",
])
def test_s3_rejects_foreign_references_before_access(key):
    backend = s3_backend()
    with pytest.raises(ValueError):
        backend.get(1, key)
    with pytest.raises(ValueError):
        backend.delete(1, key)
    backend._client.get_object.assert_not_called()
    backend._client.delete_object.assert_not_called()


def test_s3_purge_processes_all_pages_and_reports_partial_failure():
    backend = s3_backend()
    pages = [
        {"Contents": [{"Key": f"tenants/1/datasets/{i}.csv"} for i in range(1000)]},
        {"Contents": [{"Key": "tenants/1/datasets/1000.csv"}]},
    ]
    backend._client.get_paginator.return_value.paginate.return_value = pages
    backend._client.delete_objects.return_value = {}
    assert backend.delete_all(1)
    assert backend._client.delete_objects.call_count == 2
    backend._client.get_paginator.return_value.paginate.assert_called_with(
        Bucket="test-bucket", Prefix="tenants/1/datasets/"
    )
    backend._client.delete_objects.return_value = {"Errors": [{"Code": "AccessDenied"}]}
    with pytest.raises(OSError):
        backend.delete_all(1)


def test_storage_dispatches_by_reference_without_basename_fallback(monkeypatch):
    service = StorageService()
    service._db_backend = Mock()
    service._local_backend = Mock()
    service._db_backend.get.return_value = b"stored"
    monkeypatch.setattr(service, "_get_active_backend", lambda: service._local_backend)
    assert service.get_dataset(1, "db://tenants/1/datasets/data.csv") == b"stored"
    service._local_backend.get.assert_not_called()
    service.delete_dataset(1, "db://tenants/1/datasets/data.csv")
    service._db_backend.delete.assert_called_once()
    service._local_backend.delete.assert_not_called()
