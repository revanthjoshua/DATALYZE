from typing import Optional
from fastapi import Depends, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationException, TenantIsolationException, PermissionDeniedException
from app.models.user import User
from app.models.company import Company

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    actual_token = token
    if not actual_token and authorization and authorization.startswith("Bearer "):
        actual_token = authorization.split(" ")[1]

    if not actual_token:
        raise AuthenticationException("Authorization token is missing")

    payload = decode_access_token(actual_token)
    if not payload or "sub" not in payload:
        raise AuthenticationException("Invalid or expired authentication token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationException("User account does not exist")

    if not user.is_active:
        raise AuthenticationException("User account is inactive")

    return user


def get_current_tenant_id(
    current_user: User = Depends(get_current_user)
) -> int:
    if not current_user.company_id:
        raise TenantIsolationException("No tenant associated with this user session")
    return current_user.company_id


def require_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces server-side Role-Based Access Control (RBAC) for Admin-only actions"""
    role = (current_user.role or "").lower()
    if role not in ["company admin", "company_admin", "admin", "platform super admin", "super_admin"]:
        raise PermissionDeniedException("Forbidden: Company Admin privileges required for this action.")
    return current_user


def require_analyst_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces server-side RBAC for Analyst, Manager, or Admin users (excludes Viewer from writes)"""
    role = (current_user.role or "").lower()
    if role in ["viewer"]:
        raise PermissionDeniedException("Forbidden: Read-only Viewer role cannot perform modifying actions.")
    return current_user
