from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.uploaded_dataset import UploadedDataset
from app.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository[UploadedDataset]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(UploadedDataset, db, tenant_id=tenant_id)

    def get_active_dataset(self) -> Optional[UploadedDataset]:
        """Returns the most recent active uploaded dataset for this tenant."""
        return (
            self._tenant_query()
            .order_by(desc(UploadedDataset.created_at))
            .first()
        )

    def record_dataset(
        self,
        filename: str,
        row_count: int,
        col_count: int,
        file_hash: Optional[str] = None,
        schema_metadata: Optional[List[Dict[str, Any]]] = None,
        detected_profile: Optional[Dict[str, Any]] = None,
        storage_path: Optional[str] = None,
        source_type: str = "upload"
    ) -> UploadedDataset:
        """Creates and stores persistent dataset record for tenant."""
        dataset = UploadedDataset(
            company_id=self.tenant_id,
            filename=filename,
            file_hash=file_hash,
            row_count=row_count,
            col_count=col_count,
            schema_metadata=schema_metadata,
            detected_profile=detected_profile,
            storage_path=storage_path,
            source_type=source_type
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def delete_all_datasets(self) -> int:
        """Deletes all dataset metadata records for current tenant."""
        count = self._tenant_query().delete()
        self.db.commit()
        return count
