import os
import zlib
import shutil
import logging
import ntpath
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger("datalyze.storage")


class BaseStorageBackend(ABC):
    """Abstract interface for tenant dataset file persistence."""

    @abstractmethod
    def save(
        self,
        tenant_id: int,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        """Saves file and returns a persistent storage reference key/path."""
        pass

    @abstractmethod
    def get(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> Optional[bytes]:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def delete(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> bool:
        """Deletes specific file."""
        pass

    @abstractmethod
    def delete_all(
        self,
        tenant_id: int,
        db: Optional[Session] = None
    ) -> bool:
        """Purges all files belonging to a tenant."""
        pass


def _tenant_id(tenant_id: int) -> int:
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int) or tenant_id < 1:
        raise ValueError("A positive tenant ID is required for storage access")
    return tenant_id


def _filename(filename: str) -> str:
    # Reject both Windows and POSIX traversal even on a different host OS.
    if (not isinstance(filename, str) or not filename or filename in {".", ".."}
            or filename != ntpath.basename(filename) or "/" in filename
            or any(char in filename for char in ':<>"|?*\x00')
            or any(ord(char) < 32 for char in filename)
            or filename.endswith((".", " "))):
        raise ValueError("Storage filename must be a single safe file name")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    if filename.split(".", 1)[0].upper() in reserved:
        raise ValueError("Reserved storage filename")
    return filename


def _object_key(tenant_id: int, storage_key: str, scheme: str, bucket: str = "") -> str:
    prefix = f"tenants/{_tenant_id(tenant_id)}/datasets/"
    uri_prefix = f"{scheme}://{bucket + '/' if bucket else ''}"
    if storage_key.startswith(uri_prefix):
        key = storage_key[len(uri_prefix):]
    elif "://" in storage_key:
        raise ValueError("Storage reference belongs to a different backend or bucket")
    elif "/" not in storage_key and "\\" not in storage_key:
        key = prefix + _filename(storage_key)
    else:
        key = storage_key
    if not key.startswith(prefix):
        raise ValueError("Storage reference does not belong to this tenant")
    _filename(key[len(prefix):])
    return key


class LocalStorageBackend(BaseStorageBackend):
    """Dataset files constrained to the authenticated tenant's storage directory."""

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = str(Path(base_dir).resolve())

    def _get_tenant_dir(self, tenant_id: int) -> Path:
        base = Path(self.base_dir)
        tenant_root = base / "tenants" / str(_tenant_id(tenant_id))
        # Refuse symlink/junction redirection even to another tenant within storage.
        expected = tenant_root / "datasets"
        if expected.resolve() != expected or not expected.is_relative_to(base):
            raise ValueError("Tenant storage directory is outside its expected location")
        return expected

    def _resolve_key(self, tenant_id: int, storage_key: str) -> Path:
        tenant_dir = self._get_tenant_dir(tenant_id)
        if "://" in storage_key:
            raise ValueError("Expected a local storage reference")
        if storage_key == ntpath.basename(storage_key) and "/" not in storage_key:
            path = tenant_dir / _filename(storage_key)
        else:
            path = Path(storage_key).absolute()
        resolved = path.resolve()
        # Only direct dataset files may be read or removed. Resolving here also
        # detects an existing symlink file that points beyond the tenant directory.
        if resolved.parent != tenant_dir or path.is_symlink():
            raise ValueError("Storage reference does not belong to this tenant")
        _filename(resolved.name)
        return resolved

    def save(self, tenant_id: int, filename: str, content: bytes,
             content_type: str = "text/csv", db: Optional[Session] = None) -> str:
        tenant_dir = self._get_tenant_dir(tenant_id)
        path = self._resolve_key(tenant_id, _filename(filename))
        tenant_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def get(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> Optional[bytes]:
        path = self._resolve_key(tenant_id, storage_key)
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None

    def delete(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> bool:
        path = self._resolve_key(tenant_id, storage_key)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False

    def delete_all(self, tenant_id: int, db: Optional[Session] = None) -> bool:
        tenant_dir = self._get_tenant_dir(tenant_id)
        # Verify the resolved absolute target immediately before recursive deletion.
        if tenant_dir.resolve() != tenant_dir:
            raise ValueError("Tenant storage directory was redirected")
        if tenant_dir.exists():
            shutil.rmtree(tenant_dir)
        return True


class DatabaseStorageBackend(BaseStorageBackend):
    """
    Database-backed persistent storage suitable for serverless hosts.
    Stores compressed dataset binary blobs directly in Neon PostgreSQL or SQLite database.
    Persists across Vercel function invocations without external object-storage
    credentials. Database storage and transfer remain subject to the host plan.
    """

    def save(
        self,
        tenant_id: int,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        if db is None:
            from app.core.database import SessionLocal
            db_session = SessionLocal()
            close_session = True
        else:
            db_session = db
            close_session = False

        try:
            from app.models.dataset_blob import DatasetStorageBlob

            filename = _filename(filename)
            storage_key = f"db://tenants/{_tenant_id(tenant_id)}/datasets/{filename}"
            compressed = zlib.compress(content, level=6)

            # Check if record already exists for this tenant + filename
            existing = (
                db_session.query(DatasetStorageBlob)
                .filter(
                    DatasetStorageBlob.company_id == tenant_id,
                    DatasetStorageBlob.filename == filename
                )
                .first()
            )

            if existing:
                existing.compressed_data = compressed
                existing.storage_key = storage_key
                existing.content_type = content_type
                existing.size_bytes = len(content)
            else:
                new_blob = DatasetStorageBlob(
                    company_id=tenant_id,
                    filename=filename,
                    storage_key=storage_key,
                    compressed_data=compressed,
                    content_type=content_type,
                    size_bytes=len(content)
                )
                db_session.add(new_blob)

            (db_session.flush() if db_session.info.get("dataset_transaction") else db_session.commit())
            logger.info(
                f"DatabaseStorage: Persisted {len(content)} bytes (compressed: {len(compressed)} bytes) "
                f"for tenant #{tenant_id} as '{storage_key}'"
            )
            return storage_key
        except Exception as exc:
            db_session.rollback()
            logger.error(f"DatabaseStorage: Failed to save dataset blob for tenant #{tenant_id}: {exc}", exc_info=True)
            raise
        finally:
            if close_session:
                db_session.close()

    def get(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> Optional[bytes]:
        if db is None:
            from app.core.database import SessionLocal
            db_session = SessionLocal()
            close_session = True
        else:
            db_session = db
            close_session = False

        try:
            from app.models.dataset_blob import DatasetStorageBlob

            key = _object_key(tenant_id, storage_key, "db")
            storage_key = "db://" + key
            blob = (
                db_session.query(DatasetStorageBlob)
                .filter(
                    DatasetStorageBlob.company_id == tenant_id,
                    DatasetStorageBlob.storage_key == storage_key
                )
                .order_by(DatasetStorageBlob.updated_at.desc())
                .first()
            )

            if blob and blob.compressed_data:
                return zlib.decompress(blob.compressed_data)
            return None
        except Exception as exc:
            logger.error(f"DatabaseStorage: Failed to retrieve dataset blob '{storage_key}' for tenant #{tenant_id}: {exc}", exc_info=True)
            raise
        finally:
            if close_session:
                db_session.close()

    def delete(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> bool:
        if db is None:
            from app.core.database import SessionLocal
            db_session = SessionLocal()
            close_session = True
        else:
            db_session = db
            close_session = False

        try:
            from app.models.dataset_blob import DatasetStorageBlob

            key = _object_key(tenant_id, storage_key, "db")
            storage_key = "db://" + key
            deleted = (
                db_session.query(DatasetStorageBlob)
                .filter(
                    DatasetStorageBlob.company_id == tenant_id,
                    DatasetStorageBlob.storage_key == storage_key
                )
                .delete()
            )
            (db_session.flush() if db_session.info.get("dataset_transaction") else db_session.commit())
            return deleted > 0
        except Exception as exc:
            db_session.rollback()
            logger.error(f"DatabaseStorage: Error deleting blob '{storage_key}': {exc}", exc_info=True)
            raise
        finally:
            if close_session:
                db_session.close()

    def delete_all(
        self,
        tenant_id: int,
        db: Optional[Session] = None
    ) -> bool:
        if db is None:
            from app.core.database import SessionLocal
            db_session = SessionLocal()
            close_session = True
        else:
            db_session = db
            close_session = False

        try:
            from app.models.dataset_blob import DatasetStorageBlob
            deleted = db_session.query(DatasetStorageBlob).filter(DatasetStorageBlob.company_id == _tenant_id(tenant_id)).delete()
            (db_session.flush() if db_session.info.get("dataset_transaction") else db_session.commit())
            return True
        except Exception as exc:
            db_session.rollback()
            logger.error(f"DatabaseStorage: Error purging all blobs for tenant #{tenant_id}: {exc}", exc_info=True)
            raise
        finally:
            if close_session:
                db_session.close()


class S3StorageBackend(BaseStorageBackend):
    """
    S3-compatible Object Storage Backend supporting Cloudflare R2 (10GB 100% Free tier, 0 egress fees),
    AWS S3, and MinIO.
    """

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.endpoint = settings.S3_ENDPOINT_URL
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.region = settings.AWS_REGION or "auto"
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                )
            except Exception as e:
                logger.error(f"S3Storage: Failed to initialize boto3 client: {e}")
                raise
        return self._client

    def _get_key(self, tenant_id: int, filename: str) -> str:
        return f"tenants/{_tenant_id(tenant_id)}/datasets/{_filename(filename)}"

    def save(
        self,
        tenant_id: int,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        key = self._get_key(tenant_id, filename)
        s3 = self._get_client()
        s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type
        )
        return f"s3://{self.bucket}/{key}"

    def get(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> Optional[bytes]:
        key = _object_key(tenant_id, storage_key, "s3", self.bucket)
        try:
            response = self._get_client().get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            error = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if error in {"NoSuchKey", "NotFound", "404"}:
                return None
            raise

    def delete(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> bool:
        key = _object_key(tenant_id, storage_key, "s3", self.bucket)
        self._get_client().delete_object(Bucket=self.bucket, Key=key)
        return True

    def delete_all(self, tenant_id: int, db: Optional[Session] = None) -> bool:
        prefix = f"tenants/{_tenant_id(tenant_id)}/datasets/"
        client = self._get_client()
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            keys = [{"Key": _object_key(tenant_id, obj["Key"], "s3", self.bucket)}
                    for obj in page.get("Contents", [])]
            if keys:
                result = client.delete_objects(Bucket=self.bucket, Delete={"Objects": keys})
                if result.get("Errors"):
                    raise OSError("Object storage could not delete all tenant datasets")
        return True


class StorageService:
    """
    Unified Storage Service for Datalyze.
    Selects the optimal storage backend based on configuration and environment:
    - Auto selects S3 if credentials provided
    - In production/serverless, persists to the database within its storage quota
    - In local development, supports LocalStorage and DatabaseStorage
    """

    def __init__(self):
        self._local_backend = LocalStorageBackend()
        self._db_backend = DatabaseStorageBackend()
        self._s3_backend = None

    def _get_active_backend(self) -> BaseStorageBackend:
        backend_cfg = (settings.STORAGE_BACKEND or "auto").lower()

        if backend_cfg == "s3" or (backend_cfg == "auto" and settings.S3_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID):
            if self._s3_backend is None:
                self._s3_backend = S3StorageBackend()
            return self._s3_backend

        if backend_cfg == "db" or settings.ENVIRONMENT.lower() == "production" or os.getenv("VERCEL"):
            return self._db_backend

        return self._local_backend

    def save_dataset(
        self,
        tenant_id: int,
        filename: str,
        content: Union[bytes, str],
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        backend = self._get_active_backend()
        return backend.save(
            tenant_id=tenant_id,
            filename=filename,
            content=content_bytes,
            content_type=content_type,
            db=db
        )

    def _backend_for_key(self, storage_key: str) -> BaseStorageBackend:
        # Dispatch by the durable reference, not today's active backend. Trying a
        # different backend by basename can retrieve or delete a different file.
        if storage_key.startswith("db://"):
            return self._db_backend
        if storage_key.startswith("s3://"):
            if self._s3_backend is None:
                self._s3_backend = S3StorageBackend()
            return self._s3_backend
        if "/" in storage_key or "\\" in storage_key:
            return self._local_backend
        return self._get_active_backend()

    def get_dataset(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> Optional[bytes]:
        return self._backend_for_key(storage_key).get(tenant_id, storage_key, db=db)

    def delete_dataset(self, tenant_id: int, storage_key: str, db: Optional[Session] = None) -> bool:
        return self._backend_for_key(storage_key).delete(tenant_id, storage_key, db=db)

    def delete_all_tenant_datasets(self, tenant_id: int, db: Optional[Session] = None) -> bool:
        _tenant_id(tenant_id)
        active = self._get_active_backend()
        # External failures propagate before database metadata is removed.
        self._local_backend.delete_all(tenant_id=tenant_id, db=db)
        if isinstance(active, S3StorageBackend):
            active.delete_all(tenant_id=tenant_id, db=db)
        elif self._s3_backend is not None:
            self._s3_backend.delete_all(tenant_id=tenant_id, db=db)
        self._db_backend.delete_all(tenant_id=tenant_id, db=db)
        return True


storage_service = StorageService()
