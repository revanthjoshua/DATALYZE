from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class TeamInviteIn(BaseModel):
    email: EmailStr
    role: str = Field(default="Employee", description="Role to assign: Employee, Analyst, Admin")
    full_name: Optional[str] = Field(default=None, description="Colleague's Full Name")


class InvitationOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    status: str  # "pending", "accepted", "expired", "revoked"
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InviteVerifyOut(BaseModel):
    valid: bool
    email: str
    full_name: Optional[str] = None
    role: str
    company_name: str
    company_id: int


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., description="Secure Invitation Token")
    password: str = Field(..., min_length=6, description="Chosen Password")
    confirm_password: str = Field(..., min_length=6, description="Confirm Password")
    full_name: Optional[str] = Field(default=None, description="Full Name")
    phone_number: Optional[str] = Field(default=None, description="Phone Number")
