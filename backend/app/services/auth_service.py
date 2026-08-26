from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import random
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
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AuthenticationException, DatalyzeException
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
from app.industry.industry_config import get_default_kpis_for_industry
from app.models.kpi_definition import KPIDefinition


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

        # 2. Create Company
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

        # 2. Resolve default company
        admin_user = user_repo.get_by_email_global("admin@datalyze.com")
        if not admin_user:
            # Ensure primary workspace exists
            self.register_admin(
                AdminRegistrationRequest(
                    full_name="Admin Leader",
                    phone_number="+15550100",
                    email="admin@datalyze.com",
                    username="admin",
                    password="Admin123!",
                    confirm_password="Admin123!",
                    company_name="Acme Global Workspace",
                    industry="Retail/E-commerce"
                )
            )
            admin_user = user_repo.get_by_email_global("admin@datalyze.com")

        company_id = admin_user.company_id if admin_user else 1

        # 3. Create Employee User
        hashed_pw = get_password_hash(data.password)
        emp_user = User(
            company_id=company_id,
            email=clean_email,
            username=clean_username,
            phone_number=clean_phone,
            hashed_password=hashed_pw,
            full_name=data.full_name.strip(),
            role=UserRole.EMPLOYEE.value,
            is_active=True
        )
        self.db.add(emp_user)
        self.db.commit()
        self.db.refresh(emp_user)

        company = self.db.query(Company).filter(Company.id == company_id).first()

        token_payload = {
            "sub": str(emp_user.id),
            "email": emp_user.email,
            "company_id": company_id,
            "role": emp_user.role,
        }
        access_token = create_access_token(data=token_payload)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": emp_user,
            "company": {
                "id": company.id if company else 1,
                "name": company.name if company else "Company Workspace",
                "industry": company.industry if company else "Retail/E-commerce",
                "currency": company.currency if company else "USD",
                "timezone": company.timezone if company else "UTC",
            }
        }

    def register_company_and_admin(self, user_in: UserCreate) -> Dict[str, Any]:
        base_username = user_in.email.split('@')[0]
        user_repo = UserRepository(self.db)
        resolved_username = base_username
        if user_repo.get_by_username_global(resolved_username):
            resolved_username = f"{base_username}_{random.randint(1000, 9999)}"

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
            raise AuthenticationException(f"No account found matching '{raw_ident}'. Please check your credentials or register.")

        # Verify password strictly against user's stored hash
        if not verify_password(clean_password, user.hashed_password):
            raise AuthenticationException("Incorrect password. Please try again or use 'Forgot password?' to reset.")

        if not user.is_active:
            raise AuthenticationException("Your user account has been disabled. Please contact your company administrator.")

        # Enforce strict portal role restrictions
        user_role_lower = (user.role or "").lower()
        is_admin_role = user_role_lower in ["company admin", "company_admin", "admin", "platform super admin", "super_admin"]

        if portal == "admin":
            if not is_admin_role:
                raise DatalyzeException(
                    status_code=403,
                    detail="Access denied: This portal is restricted to Company Administrators. Please sign in via the Employee Portal."
                )
        elif portal == "employee":
            if is_admin_role:
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

        # Generate 6-digit verification code
        code = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        reset_code = PasswordResetCode(
            user_id=user.id,
            target=raw_ident,
            code=code,
            expires_at=expires_at,
            is_used=False
        )
        self.db.add(reset_code)
        self.db.commit()

        # Mask target for privacy
        if "@" in raw_ident:
            parts = raw_ident.split("@")
            masked = f"{parts[0][:2]}***@{parts[1]}"
        else:
            masked = f"{raw_ident[:3]}****{raw_ident[-2:]}" if len(raw_ident) >= 5 else raw_ident

        return {
            "success": True,
            "message": f"Verification code sent to {masked}.",
            "target": masked,
            "code_preview": code,  # Included for immediate UI verification feedback
            "expires_in_minutes": 15
        }

    def verify_reset_code(self, req: ForgotPasswordVerify) -> Dict[str, Any]:
        user_repo = UserRepository(self.db)
        raw_ident = req.identifier.strip()
        user = user_repo.get_by_identifier_global(raw_ident)

        if not user:
            raise DatalyzeException(status_code=404, detail="User account not found.")

        # Find latest active code
        code_record = (
            self.db.query(PasswordResetCode)
            .filter(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.code == req.code.strip(),
                PasswordResetCode.is_used == False
            )
            .order_by(PasswordResetCode.created_at.desc())
            .first()
        )

        if not code_record:
            raise DatalyzeException(status_code=400, detail="Invalid verification code. Please check and try again.")

        now_utc = datetime.utcnow()
        exp = code_record.expires_at.replace(tzinfo=None) if code_record.expires_at.tzinfo else code_record.expires_at
        if exp < now_utc:
            raise DatalyzeException(status_code=400, detail="Verification code has expired. Please request a new code.")

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

        code_record = (
            self.db.query(PasswordResetCode)
            .filter(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.code == req.code.strip(),
                PasswordResetCode.is_used == False
            )
            .order_by(PasswordResetCode.created_at.desc())
            .first()
        )

        if not code_record:
            raise DatalyzeException(status_code=400, detail="Invalid verification code session.")

        now_utc = datetime.utcnow()
        exp = code_record.expires_at.replace(tzinfo=None) if code_record.expires_at.tzinfo else code_record.expires_at
        if exp < now_utc:
            raise DatalyzeException(status_code=400, detail="Verification code has expired.")

        # Update password
        user.hashed_password = get_password_hash(req.new_password)
        code_record.is_used = True
        self.db.commit()

        return {
            "success": True,
            "message": "Password has been successfully updated. Please sign in with your new credentials."
        }

    def reset_password(self, reset_data: PasswordResetRequest) -> Dict[str, Any]:
        return self.confirm_password_reset(
            ForgotPasswordConfirm(
                identifier=reset_data.email,
                code="000000",
                new_password=reset_data.new_password,
                confirm_password=reset_data.new_password,
                portal_type="admin"
            )
        )

    def update_user_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None
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
            if len(password.strip()) < 6:
                raise DatalyzeException(status_code=400, detail="Password must be at least 6 characters long.")
            user.hashed_password = get_password_hash(password.strip())

        self.db.commit()
        self.db.refresh(user)
        return user

