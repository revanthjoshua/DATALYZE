from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        super().__init__(User, db, tenant_id=tenant_id if tenant_id is not None else 0)

    def get_by_email_global(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

    def get_by_username_global(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username.lower().strip()).first()

    def get_by_phone_global(self, phone: str) -> Optional[User]:
        clean_phone = phone.strip().replace(" ", "").replace("-", "")
        return self.db.query(User).filter(User.phone_number == clean_phone).first()

    def get_by_identifier_global(self, identifier: str) -> Optional[User]:
        """Looks up a user by email, username, or phone number globally across database"""
        clean_id = identifier.lower().strip()
        clean_phone = identifier.strip().replace(" ", "").replace("-", "")
        return self.db.query(User).filter(
            or_(
                User.email == clean_id,
                User.username == clean_id,
                User.phone_number == clean_phone
            )
        ).first()

    def get_by_email_in_tenant(self, email: str) -> Optional[User]:
        return self._tenant_query().filter(User.email == email.lower().strip()).first()

    def list_team_members(self) -> List[User]:
        return self._tenant_query().order_by(User.created_at.asc()).all()
