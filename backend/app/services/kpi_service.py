from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.kpi_repository import KPIRepository
from app.schemas.kpi_schema import (
    KPIDefinitionCreate,
    KPIDefinitionUpdate,
    KPISummaryCard,
    KPIValueOut,
)
from app.models.kpi_definition import KPIDefinition
from app.models.kpi_value import KPIValue
from app.core.exceptions import ResourceNotFoundException, DatalyzeException


class KPIService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)

    def list_kpis(self, active_only: bool = False) -> List[KPIDefinition]:
        if active_only:
            return self.kpi_repo.get_active_kpis()
        return self.kpi_repo.list_kpis()

    def get_kpi_by_id(self, kpi_id: int) -> KPIDefinition:
        kpi = self.kpi_repo.get_kpi_by_id(kpi_id)
        if not kpi:
            raise ResourceNotFoundException(f"KPIDefinition #{kpi_id}")
        return kpi

    def create_custom_kpi(self, kpi_in: KPIDefinitionCreate) -> KPIDefinition:
        existing = self.kpi_repo.get_kpi_by_key(kpi_in.key)
        if existing:
            raise DatalyzeException(status_code=400, detail=f"KPI with key '{kpi_in.key}' already exists for this company.")

        return self.kpi_repo.create_kpi(
            key=kpi_in.key,
            name=kpi_in.name,
            description=kpi_in.description,
            category=kpi_in.category,
            unit=kpi_in.unit,
            direction=kpi_in.direction,
            calculation_cadence=kpi_in.calculation_cadence,
            is_custom=True,
            is_active=True
        )

    def get_dashboard_kpi_summaries(self) -> List[KPISummaryCard]:
        active_kpis = self.kpi_repo.get_active_kpis()
        summaries: List[KPISummaryCard] = []

        for kpi in active_kpis:
            history = self.kpi_repo.get_kpi_values(kpi.id, limit=200)
            if not history:
                continue
            
            raw_vals = [float(h.value) for h in history]
            current_val = round(float(raw_vals[-1]), 2)
            prev_val: Optional[float] = None
            pct_change: Optional[float] = None
            trend_direction: str = "neutral"
            status: str = "healthy"

            if len(raw_vals) >= 2:
                prev_val = round(float(raw_vals[-2]), 2)
                last_val = round(float(raw_vals[-1]), 2)
                current_val = last_val
                if prev_val and prev_val != 0:
                    pct_change = round(((last_val - prev_val) / abs(prev_val)) * 100, 2)
                    if pct_change > 0.1:
                        trend_direction = "up"
                    elif pct_change < -0.1:
                        trend_direction = "down"
            elif len(raw_vals) == 1:
                prev_val = current_val

            # Determine status relative to KPI direction
            if pct_change is not None:
                if kpi.direction == "increase_is_good":
                    if pct_change >= 0:
                        status = "healthy"
                    elif pct_change >= -7.0:
                        status = "warning"
                    else:
                        status = "critical"
                else:  # decrease_is_good (e.g. churn)
                    if pct_change <= 0:
                        status = "healthy"
                    elif pct_change <= 7.0:
                        status = "warning"
                    else:
                        status = "critical"

            history_out = [
                KPIValueOut(
                    id=h.id,
                    company_id=h.company_id,
                    kpi_id=h.kpi_id,
                    timestamp=h.timestamp,
                    value=h.value,
                    dimension_data=h.dimension_data,
                    source_file=h.source_file,
                    created_at=h.created_at
                )
                for h in history
            ]

            summary = KPISummaryCard(
                id=kpi.id,
                key=kpi.key,
                name=kpi.name,
                description=kpi.description,
                category=kpi.category,
                unit=kpi.unit,
                direction=kpi.direction,
                current_value=current_val,
                previous_value=prev_val,
                percentage_change=pct_change,
                trend_direction=trend_direction,
                status=status,
                recent_history=history_out
            )
            summaries.append(summary)

        return summaries

    def get_kpi_time_series(
        self,
        kpi_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 180
    ) -> List[KPIValue]:
        # Validate that KPI exists and belongs to this tenant
        kpi = self.get_kpi_by_id(kpi_id)
        return self.kpi_repo.get_kpi_values(kpi.id, start_date=start_date, end_date=end_date, limit=limit)

    def update_kpi(self, kpi_id: int, kpi_update: KPIDefinitionUpdate) -> KPIDefinition:
        kpi = self.get_kpi_by_id(kpi_id)
        return self.kpi_repo.update_kpi(kpi, kpi_update)

    def delete_kpi(self, kpi_id: int) -> bool:
        kpi = self.get_kpi_by_id(kpi_id)
        return self.kpi_repo.delete_kpi(kpi)
