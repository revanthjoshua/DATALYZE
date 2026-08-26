from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.kpi_schema import (
    KPIDefinitionOut,
    KPIDefinitionCreate,
    KPIDefinitionUpdate,
    KPISummaryCard,
    KPIValueOut,
)
from app.services.kpi_service import KPIService
from app.middleware.auth_middleware import get_current_tenant_id, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/kpis", tags=["KPI Engine"])


@router.get("", response_model=List[KPIDefinitionOut])
def list_kpis(
    active_only: bool = False,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=tenant_id)
    return service.list_kpis(active_only=active_only)


@router.get("/summary", response_model=List[KPISummaryCard])
def get_dashboard_summary(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=tenant_id)
    return service.get_dashboard_kpi_summaries()


@router.post("", response_model=KPIDefinitionOut, status_code=status.HTTP_201_CREATED)
def create_custom_kpi(
    kpi_in: KPIDefinitionCreate,
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=current_user.company_id)
    return service.create_custom_kpi(kpi_in)


@router.get("/{kpi_id}", response_model=KPIDefinitionOut)
def get_kpi_detail(
    kpi_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=tenant_id)
    return service.get_kpi_by_id(kpi_id)


@router.put("/{kpi_id}", response_model=KPIDefinitionOut)
def update_kpi(
    kpi_id: int,
    kpi_in: KPIDefinitionUpdate,
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=current_user.company_id)
    return service.update_kpi(kpi_id, kpi_in)


@router.post("/{kpi_id}/toggle", response_model=KPIDefinitionOut)
def toggle_kpi_status(
    kpi_id: int,
    is_active: bool = Query(...),
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=current_user.company_id)
    return service.toggle_kpi_status(kpi_id, is_active=is_active)


@router.get("/{kpi_id}/values", response_model=List[KPIValueOut])
def get_kpi_values(
    kpi_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 180,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = KPIService(db, tenant_id=tenant_id)
    return service.get_kpi_time_series(kpi_id, start_date=start_date, end_date=end_date, limit=limit)
