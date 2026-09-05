from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.company_schema import CompanyOut, CompanyUpdate
from app.schemas.user_schema import UserOut
from app.schemas.invitation_schema import TeamInviteIn, InvitationOut
from app.services.company_service import CompanyService
from app.services.invitation_service import InvitationService
from app.middleware.auth_middleware import get_current_tenant_id, get_current_user, require_admin_user
from app.models.user import User

router = APIRouter(prefix="/company", tags=["Company & Workspace"])


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


@router.delete("/users/{user_id}", response_model=UserOut)
@router.post("/users/{user_id}/remove", response_model=UserOut)
def remove_team_member(
    user_id: int,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivates and removes a team member from the company workspace.
    Requires Company Admin privileges.
    """
    service = CompanyService(db, tenant_id=admin_user.company_id)
    return service.remove_team_member(user_id=user_id, current_admin=admin_user)



@router.post("/invite", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def invite_team_member(
    invite_in: TeamInviteIn,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Creates a pending invitation and dispatches a branded email via Resend.
    Does not create an active user until the invitation is accepted.
    """
    service = InvitationService(db, tenant_id=admin_user.company_id)
    return service.create_or_renew_invitation(
        email=invite_in.email,
        role=invite_in.role,
        full_name=invite_in.full_name or invite_in.recipient_name,
        inviter_user=admin_user
    )


@router.get("/invitations", response_model=List[InvitationOut])
def list_company_invitations(
    status: Optional[str] = None,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Lists pending, accepted, or revoked team invitations for the company.
    """
    service = InvitationService(db, tenant_id=admin_user.company_id)
    return service.list_invitations(status=status)


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationOut)
def resend_invitation(
    invitation_id: int,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Rotates invitation token, extends expiration, and dispatches a new email via Resend.
    """
    service = InvitationService(db, tenant_id=admin_user.company_id)
    return service.resend_invitation(invitation_id=invitation_id, admin_user=admin_user)


@router.post("/invitations/{invitation_id}/revoke", response_model=InvitationOut)
@router.delete("/invitations/{invitation_id}", response_model=InvitationOut)
def revoke_invitation(
    invitation_id: int,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Revokes a pending invitation so the token cannot be used.
    """
    service = InvitationService(db, tenant_id=admin_user.company_id)
    return service.revoke_invitation(invitation_id=invitation_id, admin_user=admin_user)
