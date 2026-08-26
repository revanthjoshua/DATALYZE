from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.prediction_schema import PredictionOut
from app.services.prediction_service import PredictionService
from app.middleware.auth_middleware import get_current_tenant_id, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/predictions", tags=["Prediction Engine"])


@router.get("", response_model=List[PredictionOut])
def list_predictions(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = PredictionService(db, tenant_id=tenant_id)
    return service.list_all_predictions()


@router.get("/{kpi_id}", response_model=List[PredictionOut])
@router.get("/kpi/{kpi_id}", response_model=List[PredictionOut])
def get_kpi_predictions(
    kpi_id: int,
    horizon_days: int = 7,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = PredictionService(db, tenant_id=tenant_id)
    return service.get_predictions_for_kpi(kpi_id, horizon_days=horizon_days)


@router.post("/generate", response_model=List[PredictionOut])
def trigger_forecast_generation(
    horizon_days: int = 7,
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = PredictionService(db, tenant_id=current_user.company_id)
    return service.generate_forecasts(horizon_days=horizon_days)
