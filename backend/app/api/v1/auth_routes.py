from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
    TokenOut,
    PasswordResetRequest,
    AdminRegistrationRequest,
    EmployeeRegistrationRequest,
    ForgotPasswordRequest,
    ForgotPasswordVerify,
    ForgotPasswordConfirm,
)
from app.schemas.company_schema import CompanyOut
from app.schemas.invitation_schema import InviteVerifyOut, AcceptInviteRequest
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post("/register-admin", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_admin(data: AdminRegistrationRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_admin(data)


@router.post("/register-employee", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_employee(data: EmployeeRegistrationRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_employee(data)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_company_and_admin(user_in)


@router.post("/login", response_model=TokenOut)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.authenticate_user(login_data)


@router.post("/forgot-password/request")
def request_password_reset(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.request_password_reset(req)


@router.post("/forgot-password/verify")
def verify_password_reset(req: ForgotPasswordVerify, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.verify_reset_code(req)


@router.post("/forgot-password/confirm")
def confirm_password_reset(req: ForgotPasswordConfirm, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.confirm_password_reset(req)


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.company import Company
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    return {
        "user": UserOut.model_validate(current_user),
        "company": CompanyOut.model_validate(company) if company else None
    }


@router.put("/me")
def update_current_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.company import Company
    auth_service = AuthService(db)
    updated_user = auth_service.update_user_profile(
        user_id=current_user.id,
        full_name=payload.full_name,
        email=payload.email,
        username=payload.username,
        phone_number=payload.phone_number,
        password=payload.password
    )
    company = db.query(Company).filter(Company.id == updated_user.company_id).first()
    return {
        "user": UserOut.model_validate(updated_user),
        "company": CompanyOut.model_validate(company) if company else None
    }


@router.get("/invite/verify", response_model=InviteVerifyOut)
def verify_invitation(token: str, db: Session = Depends(get_db)):
    """
    Verifies the cryptographic invitation token and returns safe workspace metadata.
    """
    service = InvitationService(db)
    return service.verify_invitation_token(token)


@router.post("/invite/accept")
def accept_invitation(req: AcceptInviteRequest, db: Session = Depends(get_db)):
    """
    Accepts the invitation, verifies chosen password, creates the active user,
    and binds the user to the company workspace and assigned role from the invitation.
    """
    service = InvitationService(db)
    return service.accept_invitation(req)

