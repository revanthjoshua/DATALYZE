import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.invitation import Invitation
from app.models.user import User
from app.models.company import Company
from app.schemas.invitation_schema import AcceptInviteRequest
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import ResourceNotFoundException, DataValidationException, TenantIsolationException
from app.core.security import hash_password
from app.core.logging import log_audit_event
from app.services.email_service import email_service


class InvitationService:
    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.inv_repo = InvitationRepository(db, tenant_id=tenant_id)
        self.user_repo = UserRepository(db, tenant_id=tenant_id)

    def create_or_renew_invitation(
        self,
        email: str,
        role: str = "Employee",
        full_name: Optional[str] = None,
        inviter_user: Optional[User] = None
    ) -> Invitation:
        """
        Creates a pending invitation or refreshes an existing pending invite,
        then dispatches a branded invitation email via Resend.
        """
        clean_email = email.lower().strip()
        clean_role = role.lower().strip()
        if clean_role not in ["employee", "analyst", "admin"]:
            clean_role = "employee"

        # 1. Verify user does not already exist
        existing_user = self.db.query(User).filter(User.email == clean_email).first()
        if existing_user:
            if existing_user.company_id == self.tenant_id:
                raise DataValidationException(f"User '{clean_email}' is already an active member of this workspace.")
            else:
                raise DataValidationException(f"User '{clean_email}' is already registered with another company workspace.")

        # 2. Get company details
        company = self.db.query(Company).filter(Company.id == self.tenant_id).first()
        company_name = company.name if company else "Datalyze Workspace"
        inviter_name = inviter_user.full_name if inviter_user else "Workspace Admin"

        # 3. Check for existing pending invitation
        existing_inv = self.inv_repo.get_pending_by_email(clean_email)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        if existing_inv:
            existing_inv.token = token
            existing_inv.expires_at = expires_at
            existing_inv.role = clean_role
            if full_name:
                existing_inv.full_name = full_name.strip()
            self.db.commit()
            self.db.refresh(existing_inv)
            invitation = existing_inv
        else:
            invitation = Invitation(
                company_id=self.tenant_id,
                email=clean_email,
                full_name=full_name.strip() if full_name else None,
                role=clean_role,
                token=token,
                expires_at=expires_at,
                status="pending"
            )
            self.db.add(invitation)
            self.db.commit()
            self.db.refresh(invitation)

        # 4. Dispatch Email via Resend
        try:
            email_service.send_invitation_email(
                to_email=clean_email,
                recipient_name=invitation.full_name or clean_email.split("@")[0].capitalize(),
                company_name=company_name,
                inviter_name=inviter_name,
                role=clean_role,
                token=token
            )
        except Exception as exc:
            # If email fails, rollback creation to avoid ghost invitations
            self.db.delete(invitation)
            self.db.commit()
            raise exc

        log_audit_event(
            event="team_invitation_created",
            details={
                "email": clean_email,
                "role": clean_role,
                "company_id": self.tenant_id,
                "invitation_id": invitation.id
            },
            level="INFO",
            status="SUCCESS"
        )

        return invitation

    def verify_invitation_token(self, token: str) -> Dict[str, Any]:
        """
        Validates the token, checks expiration and status, and returns safe metadata.
        """
        clean_token = token.strip()
        inv = self.inv_repo.get_by_token(clean_token)
        if not inv:
            raise ResourceNotFoundException("Invalid or unrecognized invitation link.")

        if inv.status == "accepted":
            raise DataValidationException("This invitation has already been accepted. Please sign in to your workspace.")

        if inv.status == "revoked":
            raise DataValidationException("This invitation has been revoked by the workspace administrator.")

        # Check expiration
        now = datetime.now(timezone.utc)
        exp = inv.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp < now:
            inv.status = "expired"
            self.db.commit()
            raise DataValidationException("This invitation has expired. Please ask your workspace administrator to resend an invite.")

        if inv.status != "pending":
            raise DataValidationException("This invitation is no longer active.")

        company = self.db.query(Company).filter(Company.id == inv.company_id).first()
        company_name = company.name if company else "Datalyze Workspace"

        return {
            "valid": True,
            "email": inv.email,
            "full_name": inv.full_name,
            "role": inv.role,
            "company_name": company_name,
            "company_id": inv.company_id
        }

    def accept_invitation(self, req: AcceptInviteRequest) -> Dict[str, Any]:
        """
        Accepts the invitation, verifies password, creates the active User account,
        and marks the invitation as accepted.
        """
        clean_token = req.token.strip()
        inv = self.inv_repo.get_by_token(clean_token)
        if not inv:
            raise ResourceNotFoundException("Invalid or unrecognized invitation link.")

        if inv.status == "accepted":
            raise DataValidationException("This invitation has already been accepted.")
        if inv.status == "revoked":
            raise DataValidationException("This invitation has been revoked by the workspace administrator.")

        now = datetime.now(timezone.utc)
        exp = inv.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < now:
            inv.status = "expired"
            self.db.commit()
            raise DataValidationException("This invitation has expired. Please request a new invitation.")

        if inv.status != "pending":
            raise DataValidationException("This invitation is no longer active.")

        # Validate passwords
        if req.password != req.confirm_password:
            raise DataValidationException("Password and Confirm Password do not match.")

        if len(req.password.strip()) < 6:
            raise DataValidationException("Password must be at least 6 characters long.")

        # Verify email is not already taken
        existing = self.db.query(User).filter(User.email == inv.email).first()
        if existing:
            inv.status = "accepted"
            self.db.commit()
            raise DataValidationException(f"An account with email '{inv.email}' is already registered.")

        # Create active user account strictly using invitation parameters
        full_name = req.full_name.strip() if req.full_name else (inv.full_name or inv.email.split("@")[0].capitalize())
        new_user = User(
            email=inv.email,
            hashed_password=hash_password(req.password.strip()),
            full_name=full_name,
            role=inv.role.lower(),
            company_id=inv.company_id,  # STRICT: securely derived from invitation record
            phone_number=req.phone_number.strip() if req.phone_number else None,
            is_active=True
        )
        self.db.add(new_user)

        # Mark invitation as accepted
        inv.status = "accepted"
        inv.accepted_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(new_user)

        company = self.db.query(Company).filter(Company.id == inv.company_id).first()
        company_name = company.name if company else "Workspace"

        log_audit_event(
            event="auth_invitation_accepted",
            details={
                "user_id": new_user.id,
                "email": new_user.email,
                "role": new_user.role,
                "company_id": new_user.company_id,
                "invitation_id": inv.id
            },
            level="INFO",
            status="SUCCESS"
        )

        return {
            "success": True,
            "message": f"Welcome to {company_name}! Your account has been activated successfully.",
            "email": new_user.email,
            "role": new_user.role,
            "company_name": company_name
        }

    def resend_invitation(self, invitation_id: int, admin_user: User) -> Invitation:
        """
        Resends an invitation with a fresh token and 7-day expiration extension.
        """
        inv = self.inv_repo.get_by_id(invitation_id)
        if not inv or inv.company_id != self.tenant_id:
            raise ResourceNotFoundException("Invitation")

        if inv.status == "accepted":
            raise DataValidationException("Cannot resend an invitation that has already been accepted.")

        company = self.db.query(Company).filter(Company.id == self.tenant_id).first()
        company_name = company.name if company else "Datalyze Workspace"
        inviter_name = admin_user.full_name or "Workspace Admin"

        # Generate new token and refresh expiry
        inv.token = secrets.token_urlsafe(32)
        inv.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        inv.status = "pending"
        self.db.commit()
        self.db.refresh(inv)

        email_service.send_invitation_email(
            to_email=inv.email,
            recipient_name=inv.full_name or inv.email.split("@")[0].capitalize(),
            company_name=company_name,
            inviter_name=inviter_name,
            role=inv.role,
            token=inv.token
        )

        log_audit_event(
            event="team_invitation_resent",
            details={"invitation_id": inv.id, "email": inv.email, "company_id": self.tenant_id},
            level="INFO",
            status="SUCCESS"
        )

        return inv

    def revoke_invitation(self, invitation_id: int, admin_user: User) -> Invitation:
        """
        Revokes an invitation, immediately invalidating the token.
        """
        inv = self.inv_repo.get_by_id(invitation_id)
        if not inv or inv.company_id != self.tenant_id:
            raise ResourceNotFoundException("Invitation")

        if inv.status == "accepted":
            raise DataValidationException("Cannot revoke an invitation that has already been accepted.")

        inv.status = "revoked"
        inv.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(inv)

        log_audit_event(
            event="team_invitation_revoked",
            details={"invitation_id": inv.id, "email": inv.email, "company_id": self.tenant_id},
            level="INFO",
            status="SUCCESS"
        )

        return inv

    def list_invitations(self, status: Optional[str] = None) -> List[Invitation]:
        return self.inv_repo.list_by_company(status=status)
