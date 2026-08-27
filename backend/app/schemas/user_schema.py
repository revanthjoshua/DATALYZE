from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    username: Optional[str] = None
    phone_number: Optional[str] = None
    role: str = "Company Admin"


class UserCreate(UserBase):
    password: str
    company_name: Optional[str] = None
    industry: Optional[str] = "Retail/E-commerce"


class AdminRegistrationRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full Name")
    phone_number: str = Field(..., min_length=6, description="Phone Number")
    email: EmailStr
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    confirm_password: str = Field(..., min_length=6, description="Confirm Password")
    company_name: Optional[str] = None
    industry: Optional[str] = "Retail/E-commerce"


class EmployeeRegistrationRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full Name")
    phone_number: str = Field(..., min_length=6, description="Phone Number")
    email: EmailStr
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    confirm_password: str = Field(..., min_length=6, description="Confirm Password")
    company_name: Optional[str] = None



class UserLogin(BaseModel):
    email: Optional[str] = None
    identifier: Optional[str] = None  # accepts email or username
    password: str
    portal_type: Optional[str] = None  # "admin" | "employee"


class ForgotPasswordRequest(BaseModel):
    identifier: str  # email or phone
    portal_type: str = "admin"  # "admin" | "employee"


class ForgotPasswordVerify(BaseModel):
    identifier: str
    code: str
    portal_type: str = "admin"


class ForgotPasswordConfirm(BaseModel):
    identifier: str
    code: str
    new_password: str
    confirm_password: str
    portal_type: str = "admin"


class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    company: Optional[dict] = None

