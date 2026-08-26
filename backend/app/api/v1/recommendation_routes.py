from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.recommendation_schema import RecommendationOut
from app.services.recommendation_service import RecommendationService
from app.middleware.auth_middleware import get_current_tenant_id, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.get("", response_model=List[RecommendationOut])
def get_recommendations(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = RecommendationService(db, tenant_id=tenant_id)
    return service.list_recommendations()


@router.post("/generate", response_model=List[RecommendationOut])
def generate_recommendations(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = RecommendationService(db, tenant_id=current_user.company_id)
    return service.generate_recommendations()


@router.post("/{rec_id}/status", response_model=RecommendationOut)
def update_recommendation_status(
    rec_id: int,
    status: str = Query(..., pattern="^(open|in_progress|completed|dismissed)$"),
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = RecommendationService(db, tenant_id=current_user.company_id)
    return service.update_status(rec_id, status)
