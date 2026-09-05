from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import secrets
import hashlib
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.company import Company
from app.models.role import UserRole
from app.models.password_reset_code import PasswordResetCode
from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    PasswordResetRequest,
    AdminRegistrationRequest,
    EmployeeRegistrationRequest,
    ForgotPasswordRequest,
    ForgotPasswordVerify,
    ForgotPasswordConfirm,
)
import logging
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AuthenticationException, DatalyzeException, BadRequestException
from app.core.logging import log_audit_event
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
from app.services.email_service import email_service

logger = logging.getLogger("datalyze.auth")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_admin(self, data: AdminRegistrationRequest) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        clean_email = data.email.lower().strip()
        clean_username = data.username.lower().strip()
        clean_phone = data.phone_number.strip().replace(" ", "").replace("-", "")

        # 1. Validation
        if data.password != data.confirm_password:
            raise DatalyzeException(status_code=400, detail="Passwords do not match. Please re-enter.")

        if len(data.password) < 6:
            raise DatalyzeException(status_code=400, detail="Password must be at least 6 characters long.")

        if user_repo.get_by_email_global(clean_email):
            raise DatalyzeException(status_code=400, detail=f"An account with email '{clean_email}' already exists.")

        if user_repo.get_by_username_global(clean_username):
            raise DatalyzeException(status_code=400, detail=f"Username '{clean_username}' is already taken. Please choose another.")

        company_name = (data.company_name or f"{data.full_name}'s Workspace").strip()
        industry = data.industry or "Retail/E-commerce"

        # 2. Create Company Workspace
        company_repo = CompanyRepository(self.db)
        company = company_repo.create_company(
            name=company_name,
            industry=industry,
            currency="USD",
            timezone="UTC"
        )

        # 3. Create Admin User
        hashed_pw = get_password_hash(data.password)
        new_user = User(
            company_id=company.id,
            email=clean_email,
            username=clean_username,
            phone_number=clean_phone,
            hashed_password=hashed_pw,
            full_name=data.full_name.strip(),
            role=UserRole.COMPANY_ADMIN.value,
            is_active=True
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        log_audit_event(
            event="auth_register_admin_success",
            details={
                "user_id": new_user.id,
                "email": clean_email,
                "username": clean_username,
                "company_id": company.id,
                "company_name": company.name,
                "role": new_user.role,
            },
            level="INFO",
            status="SUCCESS"
        )

        token_payload = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "company_id": company.id,
            "role": new_user.role,
        }
        access_token = create_access_token(data=token_payload)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user,
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "currency": company.currency,
                "timezone": company.timezone,
            }
        }

    def register_employee(self, data: EmployeeRegistrationRequest) -> Dict[str, Any]:
        """
        Employee registration is strictly invitation-driven.
        If an invitation token is provided, accepts the invitation and returns authenticated TokenOut.
        Otherwise, direct uninvited registration attempts are safely rejected with 400 Bad Request.
        """
        if data.invitation_token:
            from app.services.invitation_service import InvitationService
            from app.schemas.invitation_schema import AcceptInviteRequest
            inv_service = InvitationService(self.db)
            inv_service.accept_invitation(
                AcceptInviteRequest(
                    token=data.invitation_token,
                    password=data.password,
                    confirm_password=data.confirm_password,
                    full_name=data.full_name,
                    username=data.username,
                    phone_number=data.phone_number,
                )
            )

            # Look up newly activated user
            user_repo = UserRepository(self.db)
            new_user = user_repo.get_by_email_global(data.email)
            if not new_user:
                # If email differed from invitation, find via token
                inv = inv_service.inv_repo.get_by_token(data.invitation_token.strip())
                if inv:
                    new_user = user_repo.get_by_email_global(inv.email)

            if new_user:
                company = self.db.query(Company).filter(Company.id == new_user.company_id).first()
                token_payload = {
                    "sub": str(new_user.id),
                    "email": new_user.email,
                    "company_id": new_user.company_id,
                    "role": new_user.role,
                }
                access_token = create_access_token(data=token_payload)
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": new_user,
                    "company": {
                        "id": company.id if company else 0,
                        "name": company.name if company else "",
                        "industry": company.industry if company else "",
                        "currency": company.currency if company else "USD",
                        "timezone": company.timezone if company else "UTC",
                    }
                }

        log_audit_event(
            event="auth_register_employee_direct_attempt_blocked",
            details={"email": data.email, "company_name": data.company_name},
            level="WARNING",
            status="BLOCKED"
        )
        raise BadRequestException(
            "Direct employee registration is not permitted. Please join using the team invitation link sent by your workspace administrator."
        )

    def register_company_and_admin(self, user_in: UserCreate) -> Dict[str, Any]:
        base_username = user_in.email.split('@')[0]
        user_repo = UserRepository(self.db)
        resolved_username = base_username
        if user_repo.get_by_username_global(resolved_username):
            resolved_username = f"{base_username}_{secrets.randbelow(9000) + 1000}"

        return self.register_admin(
            AdminRegistrationRequest(
                full_name=user_in.full_name,
                phone_number="+15550100",
                email=user_in.email,
                username=resolved_username,
                password=user_in.password,
                confirm_password=user_in.password,
                company_name=user_in.company_name,
                industry=user_in.industry
            )
        )

    def authenticate_user(self, login_data: UserLogin) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        raw_ident = (login_data.identifier or login_data.email or "").strip()
        clean_password = login_data.password.strip()
        portal = (login_data.portal_type or "").lower().strip()

        if not raw_ident:
            raise AuthenticationException("Please provide your registered Email or Username.")

        if not clean_password:
            raise AuthenticationException("Please provide your password.")

        user = user_repo.get_by_identifier_global(raw_ident)
        if not user:
            log_audit_event(
                event="auth_login_failure_user_not_found",
                details={"identifier": raw_ident, "portal": portal},
                level="WARNING",
                status="FAILED"
            )
            raise AuthenticationException(f"No account found matching '{raw_ident}'. Please check your credentials or register.")

        # Verify password strictly against user's stored hash
        if not verify_password(clean_password, user.hashed_password):
            log_audit_event(
                event="auth_login_failure_invalid_password",
                details={"user_id": user.id, "identifier": raw_ident, "portal": portal},
                level="WARNING",
                status="FAILED"
            )
            raise AuthenticationException("Incorrect password. Please try again or use 'Forgot password?' to reset.")

        if not user.is_active:
            log_audit_event(
                event="auth_login_failure_user_inactive",
                details={"user_id": user.id, "identifier": raw_ident},
                level="WARNING",
                status="FAILED"
            )
            raise AuthenticationException("Your user account has been disabled. Please contact your company administrator.")

        # Enforce strict portal role restrictions
        user_role_lower = (user.role or "").lower()
        is_admin_role = user_role_lower in ["company admin", "company_admin", "admin", "platform super admin", "super_admin"]

        if portal == "admin":
            if not is_admin_role:
                log_audit_event(
                    event="auth_portal_access_denied_admin_required",
                    details={"user_id": user.id, "role": user.role, "portal": portal},
                    level="WARNING",
                    status="FORBIDDEN"
                )
                raise DatalyzeException(
                    status_code=403,
                    detail="Access denied: This portal is restricted to Company Administrators. Please sign in via the Employee Portal."
                )
        elif portal == "employee":
            if is_admin_role:
                log_audit_event(
                    event="auth_portal_access_denied_employee_required",
                    details={"user_id": user.id, "role": user.role, "portal": portal},
                    level="WARNING",
                    status="FORBIDDEN"
                )
                raise DatalyzeException(
                    status_code=403,
                    detail="Access denied: Administrator accounts must sign in via the Admin Portal."
                )

        company = self.db.query(Company).filter(Company.id == user.company_id).first()
        if not company or not company.is_active:
            raise AuthenticationException("Company workspace is disabled or inactive.")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "company_id": user.company_id,
            "role": user.role,
        }
        access_token = create_access_token(data=token_payload)

        log_audit_event(
            event="auth_login_success",
            details={
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "company_id": user.company_id,
                "role": user.role,
                "portal": portal or "default",
            },
            level="INFO",
            status="SUCCESS"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "currency": company.currency,
                "timezone": company.timezone,
            }
        }

    def request_password_reset(self, req: ForgotPasswordRequest) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        raw_ident = req.identifier.strip()
        portal = (req.portal_type or "admin").lower().strip()

        if not raw_ident:
            raise DatalyzeException(status_code=400, detail="Please provide your registered Email or Phone Number.")

        user = user_repo.get_by_identifier_global(raw_ident)
        if not user:
            raise DatalyzeException(
                status_code=404,
                detail=f"No {portal.title()} account found matching '{raw_ident}'."
            )

        # Check role match
        user_role_lower = (user.role or "").lower()
        is_admin = user_role_lower in ["company admin", "company_admin", "admin", "platform super admin", "super_admin"]
        if portal == "admin" and not is_admin:
            raise DatalyzeException(
                status_code=403,
                detail="Account is registered as an Employee. Please use the Employee Forgot Password page."
            )
        elif portal == "employee" and is_admin:
            raise DatalyzeException(
                status_code=403,
                detail="Account is registered as an Administrator. Please use the Admin Forgot Password page."
            )

        # 1. Invalidate any prior unused reset codes for this user
        self.db.query(PasswordResetCode).filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.is_used == False
        ).update({"is_used": True})

        # 2. Cryptographically secure 6-digit verification code generation
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        # 3. Store hashed code in database
        reset_code = PasswordResetCode(
            user_id=user.id,
            target=raw_ident,
            code=code_hash,
            expires_at=expires_at,
            is_used=False
        )
        self.db.add(reset_code)
        self.db.commit()

        # 4. Dispatch verification code via Resend transactional email
        delivery = email_service.send_password_reset_otp_email(
            to_email=user.email,
            recipient_name=user.full_name,
            otp_code=code,
            expires_in_minutes=15
        )
        if not delivery.get("success"):
            if settings.ENVIRONMENT == "production":
                self.db.delete(reset_code)
                self.db.commit()
                raise DatalyzeException(
                    status_code=502,
                    detail="The verification email could not be delivered. Check the Resend production configuration and try again."
                )
            else:
                logger.warning(f"Resend OTP delivery simulated for development/test: {delivery.get('error')}")

        # 5. Mask target for privacy
        if "@" in raw_ident:
            parts = raw_ident.split("@")
            masked = f"{parts[0][:2]}***@{parts[1]}"
        else:
            masked = f"{raw_ident[:3]}****{raw_ident[-2:]}" if len(raw_ident) >= 5 else raw_ident

        log_audit_event(
            event="auth_password_reset_code_generated",
            details={"user_id": user.id, "target": masked, "portal": portal},
            level="INFO",
            status="SUCCESS"
        )

        return {
            "success": True,
            "message": f"Verification code sent to {masked}.",
            "target": masked,
            "expires_in_minutes": 15
        }

    def verify_reset_code(self, req: ForgotPasswordVerify) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        raw_ident = req.identifier.strip()
        user = user_repo.get_by_identifier_global(raw_ident)

        if not user:
            raise DatalyzeException(status_code=404, detail="User account not found.")

        # Compute hash of submitted code
        code_hash = hashlib.sha256(req.code.strip().encode("utf-8")).hexdigest()

        # Find matching unused code record
        code_record = (
            self.db.query(PasswordResetCode)
            .filter(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.code == code_hash,
                PasswordResetCode.is_used == False
            )
            .order_by(PasswordResetCode.created_at.desc())
            .first()
        )

        if not code_record:
            log_audit_event(
                event="auth_password_reset_verify_failed_invalid_code",
                details={"user_id": user.id},
                level="WARNING",
                status="FAILED"
            )
            raise DatalyzeException(status_code=400, detail="Invalid verification code. Please check and try again.")

        now_utc = datetime.now(timezone.utc)
        exp = code_record.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
            
        if exp < now_utc:
            log_audit_event(
                event="auth_password_reset_verify_failed_expired",
                details={"user_id": user.id},
                level="WARNING",
                status="FAILED"
            )
            raise DatalyzeException(status_code=400, detail="Verification code has expired. Please request a new code.")

        log_audit_event(
            event="auth_password_reset_code_verified",
            details={"user_id": user.id},
            level="INFO",
            status="SUCCESS"
        )

        return {
            "success": True,
            "valid": True,
            "message": "Identity verified successfully. You may now set a new password."
        }

    def confirm_password_reset(self, req: ForgotPasswordConfirm) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        raw_ident = req.identifier.strip()
        user = user_repo.get_by_identifier_global(raw_ident)

        if not user:
            raise DatalyzeException(status_code=404, detail="User account not found.")

        if req.new_password != req.confirm_password:
            raise DatalyzeException(status_code=400, detail="New passwords do not match.")

        if len(req.new_password) < 6:
            raise DatalyzeException(status_code=400, detail="Password must be at least 6 characters long.")

        code_hash = hashlib.sha256(req.code.strip().encode("utf-8")).hexdigest()

        code_record = (
            self.db.query(PasswordResetCode)
            .filter(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.code == code_hash,
                PasswordResetCode.is_used == False
            )
            .order_by(PasswordResetCode.created_at.desc())
            .first()
        )

        if not code_record:
            log_audit_event(
                event="auth_password_reset_confirm_failed_invalid_code",
                details={"user_id": user.id},
                level="WARNING",
                status="FAILED"
            )
            raise DatalyzeException(status_code=400, detail="Invalid verification code session.")

        now_utc = datetime.now(timezone.utc)
        exp = code_record.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
            
        if exp < now_utc:
            log_audit_event(
                event="auth_password_reset_confirm_failed_expired",
                details={"user_id": user.id},
                level="WARNING",
                status="FAILED"
            )
            raise DatalyzeException(status_code=400, detail="Verification code has expired.")

        # Update password with secure PBKDF2 hash and mark code as used
        user.hashed_password = get_password_hash(req.new_password)
        code_record.is_used = True
        self.db.commit()

        log_audit_event(
            event="auth_password_reset_successful",
            details={"user_id": user.id, "email": user.email},
            level="INFO",
            status="SUCCESS"
        )

        return {
            "success": True,
            "message": "Password has been successfully updated. Please sign in with your new credentials."
        }

    def update_user_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
        current_password: Optional[str] = None
    ) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise DatalyzeException(status_code=404, detail="User account not found.")

        if full_name and full_name.strip():
            user.full_name = full_name.strip()

        if username and username.strip():
            clean_u = username.lower().strip()
            if clean_u != (user.username or ""):
                existing = self.db.query(User).filter(User.username == clean_u, User.id != user_id).first()
                if existing:
                    raise DatalyzeException(status_code=400, detail="Username is already taken.")
                user.username = clean_u

        if phone_number and phone_number.strip():
            user.phone_number = phone_number.strip().replace(" ", "").replace("-", "")

        if email and email.strip():
            clean_email = email.lower().strip()
            if clean_email != user.email:
                existing = self.db.query(User).filter(User.email == clean_email, User.id != user_id).first()
                if existing:
                    raise DatalyzeException(status_code=400, detail="This email address is already in use by another account.")
                user.email = clean_email

        if password and password.strip():
            if not current_password or not verify_password(current_password, user.hashed_password):
                raise DatalyzeException(status_code=400, detail="Current password is incorrect.")
            if len(password.strip()) < 6:
                raise DatalyzeException(status_code=400, detail="Password must be at least 6 characters long.")
            user.hashed_password = get_password_hash(password.strip())

        self.db.commit()
        self.db.refresh(user)

        log_audit_event(
            event="auth_user_profile_updated",
            details={
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
            },
            level="INFO",
            status="SUCCESS"
        )
        return user

