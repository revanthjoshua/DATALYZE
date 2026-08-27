from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.invitation import Invitation
from app.repositories.base_repository import BaseRepository


class InvitationRepository(BaseRepository[Invitation]):
    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        # Allow tenant_id to be None for public token lookup during acceptance
        self.model = Invitation
        self.db = db
        self.tenant_id = tenant_id

    def get_by_token(self, token: str) -> Optional[Invitation]:
        """Fetch invitation globally by unique token"""
        return self.db.query(Invitation).filter(Invitation.token == token).first()

    def get_pending_by_email(self, email: str) -> Optional[Invitation]:
        """Fetch pending invitation for this tenant and email"""
        if self.tenant_id is None:
            return None
        return (
            self.db.query(Invitation)
            .filter(
                Invitation.company_id == self.tenant_id,
                Invitation.email == email.lower().strip(),
                Invitation.status == "pending"
            )
            .first()
        )

    def list_by_company(self, status: Optional[str] = None) -> List[Invitation]:
        """Fetch all invitations for the company, optionally filtered by status"""
        if self.tenant_id is None:
            return []
        query = self.db.query(Invitation).filter(Invitation.company_id == self.tenant_id)
        if status:
            query = query.filter(Invitation.status == status)
        return query.order_by(desc(Invitation.created_at)).all()
