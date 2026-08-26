from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.inventory_schema import InventoryDashboardSummary
from app.services.inventory_service import InventoryService
from app.middleware.auth_middleware import get_current_tenant_id, require_analyst_user
from app.models.user import User

router = APIRouter(prefix="/inventory", tags=["Smart Inventory Intelligence"])


@router.get("/summary", response_model=InventoryDashboardSummary)
def get_inventory_summary(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = InventoryService(db, tenant_id=tenant_id)
    return service.get_inventory_summary()


@router.post("/transfers/{item_id}/approve", response_model=Dict[str, Any])
def approve_inventory_transfer(
    item_id: int,
    quantity: int = 50,
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = InventoryService(db, tenant_id=current_user.company_id)
    return service.approve_transfer(item_id, quantity=quantity)


@router.post("/reseed-sample", response_model=InventoryDashboardSummary)
@router.post("/reseed", response_model=InventoryDashboardSummary)
def reseed_sample_inventory(
    current_user: User = Depends(require_analyst_user),
    db: Session = Depends(get_db)
):
    service = InventoryService(db, tenant_id=current_user.company_id)
    service.seed_sample_inventory_if_empty()
    return service.get_inventory_summary()
