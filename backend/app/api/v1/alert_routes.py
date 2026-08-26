from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.alert_schema import AlertOut
from app.services.notification_service import NotificationService
from app.middleware.auth_middleware import get_current_tenant_id

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])


@router.get("", response_model=List[AlertOut])
def get_alerts(
    unread_only: bool = False,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = NotificationService(db, tenant_id=tenant_id)
    return service.list_alerts(unread_only=unread_only)


@router.post("/mark-all-read")
def mark_all_read(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = NotificationService(db, tenant_id=tenant_id)
    count = service.mark_all_read()
    return {"marked_as_read": count}
