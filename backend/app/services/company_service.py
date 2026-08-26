from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.user import User
from app.schemas.company_schema import CompanyUpdate
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException, DataValidationException
from app.core.security import hash_password
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.industry.industry_config import get_default_kpis_for_industry
from app.models.kpi_definition import KPIDefinition


class CompanyService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.company_repo = CompanyRepository(db, tenant_id=tenant_id)
        self.user_repo = UserRepository(db, tenant_id=tenant_id)

    def get_company_profile(self) -> Company:
        company = self.company_repo.get_by_id(self.tenant_id)
        if not company:
            raise ResourceNotFoundException("Company")
        return company

    def update_company_profile(self, company_in: CompanyUpdate) -> Company:
        company = self.get_company_profile()
        update_data = company_in.model_dump(exclude_unset=True)
        
        # If industry changed, sync KPI template for that specific industry
        if "industry" in update_data and update_data["industry"] != company.industry:
            self._sync_industry_kpis(company.id, update_data["industry"])
            
        return self.company_repo.update(company, update_data)

    def list_team_members(self) -> List[User]:
        return self.user_repo.list_team_members()

    def invite_team_member(self, email: str, role: str = "analyst", full_name: Optional[str] = None) -> User:
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            if existing.company_id == self.tenant_id:
                raise DataValidationException(f"User '{email}' is already a member of this workspace.")
            else:
                raise DataValidationException(f"User '{email}' is already registered with another company.")

        new_user = User(
            email=email,
            hashed_password=hash_password("TemporaryPass123!"),
            full_name=full_name or email.split("@")[0].capitalize(),
            role=role.lower(),
            company_id=self.tenant_id,
            is_active=True
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def _sync_industry_kpis(self, company_id: int, new_industry: str):
        default_kpis = get_default_kpis_for_industry(new_industry)
        existing_keys = {k.key for k in self.db.query(KPIDefinition).filter(KPIDefinition.company_id == company_id).all()}
        
        for kpi_spec in default_kpis:
            if kpi_spec["key"] not in existing_keys:
                kpi_def = KPIDefinition(
                    company_id=company_id,
                    key=kpi_spec["key"],
                    name=kpi_spec["name"],
                    description=kpi_spec.get("description"),
                    category=kpi_spec.get("category", "General"),
                    unit=kpi_spec.get("unit", "currency"),
                    direction=kpi_spec.get("direction", "increase_is_good"),
                    calculation_cadence=kpi_spec.get("calculation_cadence", "daily"),
                    is_active=True,
                    is_custom=False
                )
                self.db.add(kpi_def)
        self.db.commit()

    def get_detected_profile(self) -> Dict[str, Any]:
        from app.services.dataset_store import TenantDatasetStore
        profile = TenantDatasetStore.get_detected_profile(self.tenant_id)
        if not profile:
            meta = TenantDatasetStore.get_metadata(self.tenant_id)
            if meta:
                profile = meta.get("detected_profile") or {}
        return profile or {}

    def auto_adapt_company_profile(self) -> Company:
        profile = self.get_detected_profile()
        company = self.get_company_profile()
        if profile:
            if profile.get("currency"):
                company.currency = profile["currency"]
            if profile.get("industry"):
                company.industry = profile["industry"]
                self._sync_industry_kpis(company.id, profile["industry"])
            if profile.get("company_name"):
                company.name = profile["company_name"]
            self.db.commit()
            self.db.refresh(company)
        return company
