from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.detection_schema import DetectionEventOut, RootCauseResultOut
from app.services.detection_service import DetectionService
from app.services.root_cause_service import RootCauseService
from app.middleware.auth_middleware import get_current_tenant_id, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/detections", tags=["Detection & Root-Cause"])


@router.get("", response_model=List[DetectionEventOut])
def get_detections(
    limit: int = 100,
    active_only: bool = False,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = DetectionService(db, tenant_id=tenant_id)
    return service.list_detections(limit=limit, active_only=active_only)


@router.post("/run", response_model=List[DetectionEventOut])
def run_anomaly_detection(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = DetectionService(db, tenant_id=current_user.company_id)
    return service.run_detection_pipeline()


@router.get("/{detection_id}/root-causes", response_model=List[RootCauseResultOut])
def get_root_causes(
    detection_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = RootCauseService(db, tenant_id=tenant_id)
    return service.get_root_causes_for_detection(detection_id)


@router.post("/acknowledge-all", response_model=Dict[str, Any])
def acknowledge_all_detections(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = DetectionService(db, tenant_id=current_user.company_id)
    count = service.acknowledge_all_detections()
    return {"message": f"Acknowledged {count} active anomalies.", "acknowledged_count": count}


@router.post("/test-anomaly", response_model=DetectionEventOut)
def trigger_test_anomaly(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = DetectionService(db, tenant_id=current_user.company_id)
    return service.create_test_anomaly()


@router.post("/{detection_id}/acknowledge", response_model=DetectionEventOut)
def acknowledge_detection(
    detection_id: int,
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = DetectionService(db, tenant_id=current_user.company_id)
    return service.acknowledge_detection(detection_id)
