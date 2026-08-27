from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.user import User
from app.schemas.company_schema import CompanyUpdate
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException, DataValidationException
from app.core.security import hash_password
from app.core.logging import log_audit_event
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

    def remove_team_member(self, user_id: int, current_admin: User) -> User:
        """
        Deactivates a team member, revoking immediate access to the workspace and all protected APIs.
        Safely enforces that a company workspace must never be left without an active Admin.
        """
        target_user = self.user_repo.get_by_id(user_id)
        if not target_user or not target_user.is_active:
            raise ResourceNotFoundException("Team member")

        # Normalize role
        target_role = (target_user.role or "").lower().strip()
        admin_roles = ["company admin", "company_admin", "admin", "platform super admin", "super_admin"]
        is_target_admin = target_role in admin_roles

        if is_target_admin:
            # Query all active admins in this tenant
            active_users = self.db.query(User).filter(
                User.company_id == self.tenant_id,
                User.is_active == True
            ).all()
            active_admin_ids = [
                u.id for u in active_users
                if (u.role or "").lower().strip() in admin_roles
            ]

            if len(active_admin_ids) <= 1 and target_user.id in active_admin_ids:
                raise DataValidationException(
                    "Cannot remove the only remaining Company Admin. Your workspace must have at least one active Admin."
                )

        # Deactivate user
        target_user.is_active = False
        self.db.commit()
        self.db.refresh(target_user)

        log_audit_event(
            event="team_member_removed",
            details={
                "company_id": self.tenant_id,
                "removed_user_id": target_user.id,
                "removed_email": target_user.email,
                "removed_role": target_user.role,
                "removed_by_user_id": current_admin.id,
                "self_removed": (target_user.id == current_admin.id)
            },
            level="INFO",
            status="SUCCESS"
        )

        return target_user

