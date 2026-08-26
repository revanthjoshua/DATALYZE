from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    industry: str = "Retail/E-commerce"
    currency: str = "USD"
    timezone: str = "UTC"


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyOut(CompanyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
