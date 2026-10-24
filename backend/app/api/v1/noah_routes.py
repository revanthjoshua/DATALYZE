from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.noah_schema import (
    NoahQueryRequest,
    NoahQueryResponse,
    NoahAgenticPlanRequest,
    NoahAgenticPlanResponse
)
from app.services.noah_service import NoahService
from app.middleware.auth_middleware import get_current_tenant_id

router = APIRouter(prefix="/noah", tags=["Dataset Assistant"])


@router.post("/query", response_model=NoahQueryResponse)
def query_noah(
    request: NoahQueryRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = NoahService(db, tenant_id=tenant_id)
    return service.process_query(request)


@router.post("/agentic-reasoning", response_model=NoahAgenticPlanResponse)
def run_agentic_reasoning(
    request: NoahAgenticPlanRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    # Gated for MVP Phase: Agentic workflow execution requires Phase 5 guardrails & audit logging
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Autonomous execution is unavailable. Use the analyst workspace to run and review evidence."
    )
