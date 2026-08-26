from typing import Optional
from sqlalchemy.orm import Session
from app.models.company import Company
from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        # If tenant_id not yet assigned (registration), allow initial setup
        super().__init__(Company, db, tenant_id=tenant_id if tenant_id is not None else 0)

    def get_by_id(self, company_id: int) -> Optional[Company]:
        return self.db.query(Company).filter(Company.id == company_id).first()

    def create_company(self, name: str, industry: str = "Retail/E-commerce", currency: str = "USD", timezone: str = "UTC") -> Company:
        company = Company(
            name=name,
            industry=industry,
            currency=currency,
            timezone=timezone,
            is_active=True
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company
