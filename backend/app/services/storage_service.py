import os
import zlib
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import log_audit_event

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


class LocalStorageBackend(BaseStorageBackend):
    """
    Filesystem storage for local development and offline environments.
    Stores files under storage/tenants/{tenant_id}/datasets/{filename}.
    """

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir

    def _get_tenant_dir(self, tenant_id: int) -> str:
        return os.path.join(self.base_dir, "tenants", str(tenant_id), "datasets")

    def save(
        self,
        tenant_id: int,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        tenant_dir = self._get_tenant_dir(tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        file_path = os.path.join(tenant_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"LocalStorage: Saved {len(content)} bytes for tenant #{tenant_id} to {file_path}")
        return file_path

    def get(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> Optional[bytes]:
        # Handle both relative/absolute paths or raw filenames
        path = storage_key
        if not os.path.exists(path):
            path = os.path.join(self._get_tenant_dir(tenant_id), os.path.basename(storage_key))
        
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def delete(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> bool:
        path = storage_key
        if not os.path.exists(path):
            path = os.path.join(self._get_tenant_dir(tenant_id), os.path.basename(storage_key))
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                logger.warning(f"LocalStorage: Error deleting {path}: {e}")
        return False

    def delete_all(
        self,
        tenant_id: int,
        db: Optional[Session] = None
    ) -> bool:
        tenant_dir = os.path.join(self.base_dir, "tenants", str(tenant_id))
        if os.path.exists(tenant_dir):
            try:
                shutil.rmtree(tenant_dir, ignore_errors=True)
                return True
            except Exception as e:
                logger.warning(f"LocalStorage: Error purging tenant dir {tenant_dir}: {e}")
        return False


class DatabaseStorageBackend(BaseStorageBackend):
    """
    100% Free, Serverless-Compatible Persistent Storage.
    Stores compressed dataset binary blobs directly in Neon PostgreSQL or SQLite database.
    Guarantees cross-request dataset persistence across Vercel serverless function invocations
    without requiring any external S3/cloud storage credentials.
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

            storage_key = f"db://tenants/{tenant_id}/datasets/{filename}"
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

            db_session.commit()
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

            filename = os.path.basename(storage_key) if "/" in storage_key else storage_key
            blob = (
                db_session.query(DatasetStorageBlob)
                .filter(
                    DatasetStorageBlob.company_id == tenant_id,
                    (DatasetStorageBlob.storage_key == storage_key) | (DatasetStorageBlob.filename == filename)
                )
                .order_by(DatasetStorageBlob.updated_at.desc())
                .first()
            )

            if blob and blob.compressed_data:
                return zlib.decompress(blob.compressed_data)
            return None
        except Exception as exc:
            logger.error(f"DatabaseStorage: Failed to retrieve dataset blob '{storage_key}' for tenant #{tenant_id}: {exc}", exc_info=True)
            return None
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

            filename = os.path.basename(storage_key) if "/" in storage_key else storage_key
            deleted = (
                db_session.query(DatasetStorageBlob)
                .filter(
                    DatasetStorageBlob.company_id == tenant_id,
                    (DatasetStorageBlob.storage_key == storage_key) | (DatasetStorageBlob.filename == filename)
                )
                .delete()
            )
            db_session.commit()
            return deleted > 0
        except Exception as exc:
            db_session.rollback()
            logger.error(f"DatabaseStorage: Error deleting blob '{storage_key}': {exc}", exc_info=True)
            return False
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
            deleted = db_session.query(DatasetStorageBlob).filter(DatasetStorageBlob.company_id == tenant_id).delete()
            db_session.commit()
            return True
        except Exception as exc:
            db_session.rollback()
            logger.error(f"DatabaseStorage: Error purging all blobs for tenant #{tenant_id}: {exc}", exc_info=True)
            return False
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
        return f"tenants/{tenant_id}/datasets/{filename}"

    def save(
        self,
        tenant_id: int,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        db: Optional[Session] = None
    ) -> str:
        s3 = self._get_client()
        key = self._get_key(tenant_id, filename)
        s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type
        )
        return f"s3://{self.bucket}/{key}"

    def get(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> Optional[bytes]:
        try:
            s3 = self._get_client()
            key = storage_key.replace(f"s3://{self.bucket}/", "") if storage_key.startswith("s3://") else storage_key
            response = s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.warning(f"S3Storage: Error getting object {storage_key}: {e}")
            return None

    def delete(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> bool:
        try:
            s3 = self._get_client()
            key = storage_key.replace(f"s3://{self.bucket}/", "") if storage_key.startswith("s3://") else storage_key
            s3.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            logger.warning(f"S3Storage: Error deleting object {storage_key}: {e}")
            return False

    def delete_all(
        self,
        tenant_id: int,
        db: Optional[Session] = None
    ) -> bool:
        try:
            s3 = self._get_client()
            prefix = f"tenants/{tenant_id}/"
            objects_to_delete = s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            if "Contents" in objects_to_delete:
                delete_keys = [{"Key": obj["Key"]} for obj in objects_to_delete["Contents"]]
                s3.delete_objects(Bucket=self.bucket, Delete={"Objects": delete_keys})
            return True
        except Exception as e:
            logger.warning(f"S3Storage: Error purging tenant prefix {prefix}: {e}")
            return False


class StorageService:
    """
    Unified Storage Service for Datalyze.
    Selects the optimal storage backend based on configuration and environment:
    - Auto selects S3 if credentials provided
    - In production/serverless, persists to Database (Neon PostgreSQL) with 100% free persistence
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

    def get_dataset(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> Optional[bytes]:
        # Try active backend first
        backend = self._get_active_backend()
        data = backend.get(tenant_id=tenant_id, storage_key=storage_key, db=db)
        if data is not None:
            return data

        # Fallback to other backends if key format indicates another backend or during migrations
        if storage_key.startswith("db://"):
            return self._db_backend.get(tenant_id=tenant_id, storage_key=storage_key, db=db)
        elif os.path.exists(storage_key) or not storage_key.startswith(("s3://", "db://")):
            return self._local_backend.get(tenant_id=tenant_id, storage_key=storage_key, db=db)

        return None

    def delete_dataset(
        self,
        tenant_id: int,
        storage_key: str,
        db: Optional[Session] = None
    ) -> bool:
        backend = self._get_active_backend()
        success = backend.delete(tenant_id=tenant_id, storage_key=storage_key, db=db)
        
        # Clean local and db replicas if present
        self._local_backend.delete(tenant_id=tenant_id, storage_key=storage_key, db=db)
        self._db_backend.delete(tenant_id=tenant_id, storage_key=storage_key, db=db)
        return success

    def delete_all_tenant_datasets(
        self,
        tenant_id: int,
        db: Optional[Session] = None
    ) -> bool:
        self._local_backend.delete_all(tenant_id=tenant_id, db=db)
        self._db_backend.delete_all(tenant_id=tenant_id, db=db)
        if self._s3_backend:
            self._s3_backend.delete_all(tenant_id=tenant_id, db=db)
        return True


storage_service = StorageService()
