from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.reporting_service import ReportingService
from app.middleware.auth_middleware import get_current_tenant_id, get_current_user
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])


@router.get("/kpi-summary-csv")
def download_kpi_summary_csv(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = ReportingService(db, tenant_id=tenant_id)
    csv_str = service.generate_kpi_summary_csv(user_id=current_user.id)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=datalyze_kpi_summary.csv"}
    )


@router.get("/kpi-trend-csv/{kpi_id}")
def download_kpi_trend_csv(
    kpi_id: int,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = ReportingService(db, tenant_id=tenant_id)
    csv_str = service.generate_kpi_trend_csv(kpi_id=kpi_id, user_id=current_user.id)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=kpi_{kpi_id}_trend.csv"}
    )
