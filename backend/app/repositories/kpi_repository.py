from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.repositories.base_repository import BaseRepository


class KPIRepository(BaseRepository[KPIDefinition]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(KPIDefinition, db, tenant_id=tenant_id)

    def get_kpi_by_id(self, kpi_id: int) -> Optional[KPIDefinition]:
        return self.get_by_id(kpi_id)

    def get_kpi_by_key(self, key: str) -> Optional[KPIDefinition]:
        return self._tenant_query().filter(KPIDefinition.key == key).first()

    def get_active_kpis(self) -> List[KPIDefinition]:
        return self._tenant_query().filter(KPIDefinition.is_active == True).all()

    def list_kpis(self) -> List[KPIDefinition]:
        return self.get_all()

    def add_kpi_value(
        self,
        kpi_id: int,
        timestamp: datetime,
        value: float,
        dimension_data: Optional[Dict[str, Any]] = None,
        source_file: Optional[str] = None
    ) -> KPIValue:
        # Check if record for this KPI & timestamp already exists to avoid duplicates
        existing = (
            self.db.query(KPIValue)
            .filter(
                KPIValue.company_id == self.tenant_id,
                KPIValue.kpi_id == kpi_id,
                KPIValue.timestamp == timestamp
            )
            .first()
        )
        if existing:
            existing.value = value
            existing.dimension_data = dimension_data
            existing.source_file = source_file
            self.db.commit()
            self.db.refresh(existing)
            return existing

        kpi_val = KPIValue(
            company_id=self.tenant_id,
            kpi_id=kpi_id,
            timestamp=timestamp,
            value=value,
            dimension_data=dimension_data,
            source_file=source_file
        )
        self.db.add(kpi_val)
        self.db.commit()
        self.db.refresh(kpi_val)
    def bulk_add_kpi_values(self, values_data: List[Dict[str, Any]]) -> None:
        """
        Fast batch insertion for multiple KPI value data points with a single atomic transaction.
        """
        if not values_data:
            return
        
        objects = []
        for item in values_data:
            val = item["value"]
            # Ensure float is valid and not NaN/Inf
            try:
                clean_val = float(val) if val is not None and not np.isnan(float(val)) and not np.isinf(float(val)) else 0.0
            except Exception:
                clean_val = 0.0

            objects.append(
                KPIValue(
                    company_id=self.tenant_id,
                    kpi_id=item["kpi_id"],
                    timestamp=item["timestamp"],
                    value=round(clean_val, 2),
                    dimension_data=item.get("dimension_data"),
                    source_file=item.get("source_file")
                )
            )

        self.db.bulk_save_objects(objects)
        self.db.commit()

    def get_kpi_values(
        self,
        kpi_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 180
    ) -> List[KPIValue]:
        query = (
            self.db.query(KPIValue)
            .filter(KPIValue.company_id == self.tenant_id, KPIValue.kpi_id == kpi_id)
        )
        if start_date:
            query = query.filter(KPIValue.timestamp >= start_date)
        if end_date:
            query = query.filter(KPIValue.timestamp <= end_date)
        return query.order_by(asc(KPIValue.timestamp)).limit(limit).all()

    def get_latest_kpi_value(self, kpi_id: int) -> Optional[KPIValue]:
        return (
            self.db.query(KPIValue)
            .filter(KPIValue.company_id == self.tenant_id, KPIValue.kpi_id == kpi_id)
            .order_by(desc(KPIValue.timestamp))
            .first()
        )

    def get_all_latest_values(self) -> Dict[int, List[KPIValue]]:
        """Returns map of kpi_id to latest 2 values for percentage change computation"""
        kpis = self.get_active_kpis()
        result = {}
        for kpi in kpis:
            vals = (
                self.db.query(KPIValue)
                .filter(KPIValue.company_id == self.tenant_id, KPIValue.kpi_id == kpi.id)
                .order_by(desc(KPIValue.timestamp))
                .limit(2)
                .all()
            )
            result[kpi.id] = vals
        return result

    def clear_all_values(self) -> int:
        """Clears all historical KPI time-series values for this tenant before new ingestion"""
        deleted_count = (
            self.db.query(KPIValue)
            .filter(KPIValue.company_id == self.tenant_id)
            .delete()
        )
        self.db.commit()
        return deleted_count
