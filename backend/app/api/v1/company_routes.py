from typing import List, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.company_schema import CompanyOut, CompanyUpdate
from app.schemas.user_schema import UserOut
from app.services.company_service import CompanyService
from app.middleware.auth_middleware import get_current_tenant_id, get_current_user, require_admin_user
from app.models.user import User

router = APIRouter(prefix="/company", tags=["Company & Workspace"])


class TeamInviteIn(BaseModel):
    email: EmailStr
    role: str = "analyst"
    full_name: Optional[str] = None


@router.get("", response_model=CompanyOut)
def get_company(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=tenant_id)
    return service.get_company_profile()


@router.put("", response_model=CompanyOut)
def update_company(
    company_in: CompanyUpdate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=admin_user.company_id)
    return service.update_company_profile(company_in)


@router.get("/detected-profile")
def get_detected_business_profile(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=tenant_id)
    return service.get_detected_profile()


@router.post("/auto-adapt", response_model=CompanyOut)
def auto_adapt_company(
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=admin_user.company_id)
    return service.auto_adapt_company_profile()


@router.get("/users", response_model=List[UserOut])
def get_team_members(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=tenant_id)
    return service.list_team_members()


@router.post("/invite", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def invite_team_member(
    invite_in: TeamInviteIn,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    service = CompanyService(db, tenant_id=admin_user.company_id)
    return service.invite_team_member(
        email=invite_in.email,
        role=invite_in.role,
        full_name=invite_in.full_name
    )
