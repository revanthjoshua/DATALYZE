"""
Comprehensive End-to-End Verification Test for Remove Member Feature
-------------------------------------------------------------------
Verifies:
1. Admin removes Employee -> Employee loses access.
2. Admin removes Analyst/Manager -> Access removed.
3. Admin removes another Admin while another Admin remains -> Works.
4. Only Admin remaining -> Cannot remove themselves.
5. Non-Admin tries to remove a member -> 403 Forbidden.
6. Company A Admin cannot remove Company B user (Tenant Isolation).
7. Removed member's old token can no longer access protected endpoints (401 Inactive).
8. Removal persists after refresh and re-login (Login fails).
9. Company shared business data remains intact.
"""
import os
import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app.core.database import Base
from app.core.security import create_access_token
from app.models.company import Company
from app.models.user import User
from app.models.kpi_definition import KPIDefinition
from app.models.uploaded_dataset import UploadedDataset
from app.services.auth_service import AuthService
from app.services.company_service import CompanyService
from app.schemas.user_schema import (
    AdminRegistrationRequest,
    EmployeeRegistrationRequest,
    UserLogin,
)
from app.core.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
    DataValidationException,
    ResourceNotFoundException,
)
from app.middleware.auth_middleware import get_current_user


def run_remove_member_tests():
    test_db_file = f"test_remove_{uuid.uuid4().hex[:8]}.db"
    test_db_url = f"sqlite:///./{test_db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    print("=" * 80)
    print("  DATALYZE: REMOVE TEAM MEMBER & ACCESS REVOCATION TEST SUITE")
    print("=" * 80)

    db = TestingSessionLocal()
    try:
        auth_service = AuthService(db)

        # -------------------------------------------------------------
        # 1. Setup Company A and Company B with Multiple Roles
        # -------------------------------------------------------------
        print("\n[STEP 1] Provisioning test workspaces and team members...")

        # Company A Admin 1 (Alice)
        reg_a1 = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Alice Primary Admin",
                username="alice_admin",
                phone_number="+15550001",
                email="alice@company-a.com",
                password="AdminPassword123!",
                confirm_password="AdminPassword123!",
                company_name="Company Alpha",
                industry="Retail/E-commerce"
            )
        )
        alice = reg_a1["user"]
        company_a_id = reg_a1["company"]["id"]

        # Company A Admin 2 (Aaron)
        aaron = User(
            company_id=company_a_id,
            email="aaron.admin@company-a.com",
            username="aaron_admin",
            phone_number="+15550002",
            full_name="Aaron Co-Admin",
            role="Company Admin",
            hashed_password=alice.hashed_password,
            is_active=True
        )
        db.add(aaron)

        # Company A Employee (Eddie)
        eddie = User(
            company_id=company_a_id,
            email="eddie.employee@company-a.com",
            username="eddie_emp",
            phone_number="+15550003",
            full_name="Eddie Employee",
            role="employee",
            hashed_password=alice.hashed_password,
            is_active=True
        )
        db.add(eddie)

        # Company A Analyst (Anna)
        anna = User(
            company_id=company_a_id,
            email="anna.analyst@company-a.com",
            username="anna_analyst",
            phone_number="+15550004",
            full_name="Anna Analyst",
            role="analyst",
            hashed_password=alice.hashed_password,
            is_active=True
        )
        db.add(anna)

        # Add shared business data for Company A
        kpi_sample = KPIDefinition(
            company_id=company_a_id,
            key="revenue",
            name="Revenue",
            unit="USD",
            is_active=True
        )
        db.add(kpi_sample)

        # Company B Admin (Bob) and Employee (Ben)
        reg_b = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Bob Admin B",
                username="bob_admin_b",
                phone_number="+15550005",
                email="bob@company-b.com",
                password="AdminPassword123!",
                confirm_password="AdminPassword123!",
                company_name="Company Beta",
                industry="SaaS/Technology"
            )
        )
        bob = reg_b["user"]
        company_b_id = reg_b["company"]["id"]

        ben = User(
            company_id=company_b_id,
            email="ben.emp@company-b.com",
            username="ben_emp",
            phone_number="+15550006",
            full_name="Ben Employee",
            role="employee",
            hashed_password=bob.hashed_password,
            is_active=True
        )
        db.add(ben)
        db.commit()

        db.refresh(alice)
        db.refresh(aaron)
        db.refresh(eddie)
        db.refresh(anna)
        db.refresh(bob)
        db.refresh(ben)

        print(f"  -> Company A (ID={company_a_id}): Alice (Admin), Aaron (Admin), Eddie (Employee), Anna (Analyst)")
        print(f"  -> Company B (ID={company_b_id}): Bob (Admin), Ben (Employee)")

        company_service_a = CompanyService(db, tenant_id=company_a_id)
        company_service_b = CompanyService(db, tenant_id=company_b_id)

        # -------------------------------------------------------------
        # 2. Test Admin removes Employee (Eddie)
        # -------------------------------------------------------------
        print("\n[STEP 2] Admin Alice removes Employee Eddie...")
        eddie_token = create_access_token({"sub": str(eddie.id), "company_id": company_a_id, "role": eddie.role})

        # Verify Eddie token works before removal
        user_verified = get_current_user(token=eddie_token, authorization=None, db=db)
        assert user_verified.id == eddie.id
        print("  -> Verified Eddie's token is valid prior to removal.")

        removed_eddie = company_service_a.remove_team_member(user_id=eddie.id, current_admin=alice)
        assert removed_eddie.is_active is False
        print(f"  [PASS] Eddie successfully deactivated in DB (is_active={removed_eddie.is_active}).")

        # Verify Eddie is not in active members list
        active_members_a = company_service_a.list_team_members()
        assert eddie.id not in [m.id for m in active_members_a]
        print(f"  [PASS] Eddie no longer appears in Active Members list (Count: {len(active_members_a)}).")

        # -------------------------------------------------------------
        # 3. Test Removed Employee's Old Token Fails Immediately (401)
        # -------------------------------------------------------------
        print("\n[STEP 3] Testing access revocation for Eddie's active token...")
        try:
            get_current_user(token=eddie_token, authorization=None, db=db)
            assert False, "Eddie's old token should have been rejected!"
        except AuthenticationException as exc:
            print(f"  [PASS] Token immediately rejected with 401: {exc.detail}")

        # -------------------------------------------------------------
        # 4. Test Removed Employee Re-Login Fails (Disabled)
        # -------------------------------------------------------------
        print("\n[STEP 4] Testing re-login attempt for Eddie...")
        try:
            auth_service.authenticate_user(
                UserLogin(
                    email="eddie.employee@company-a.com",
                    password="AdminPassword123!",
                    portal_type="employee"
                )
            )
            assert False, "Login for deactivated user must fail"
        except AuthenticationException as exc:
            print(f"  [PASS] Login attempt cleanly blocked: {exc.detail}")

        # -------------------------------------------------------------
        # 5. Test Admin removes Analyst (Anna)
        # -------------------------------------------------------------
        print("\n[STEP 5] Admin Alice removes Analyst Anna...")
        removed_anna = company_service_a.remove_team_member(user_id=anna.id, current_admin=alice)
        assert removed_anna.is_active is False
        assert anna.id not in [m.id for m in company_service_a.list_team_members()]
        print("  [PASS] Analyst Anna deactivated and removed from active list.")

        # -------------------------------------------------------------
        # 6. Test Admin removes Co-Admin (Aaron) while Alice remains
        # -------------------------------------------------------------
        print("\n[STEP 6] Admin Alice removes Co-Admin Aaron (Multiple Admins Exist)...")
        removed_aaron = company_service_a.remove_team_member(user_id=aaron.id, current_admin=alice)
        assert removed_aaron.is_active is False
        assert aaron.id not in [m.id for m in company_service_a.list_team_members()]
        print("  [PASS] Co-Admin Aaron successfully removed because Alice remains as active Admin.")

        # -------------------------------------------------------------
        # 7. Test Last Remaining Admin cannot remove themselves
        # -------------------------------------------------------------
        print("\n[STEP 7] Testing Last Remaining Admin (Alice) self-removal safety block...")
        try:
            company_service_a.remove_team_member(user_id=alice.id, current_admin=alice)
            assert False, "Should block removing the only remaining Company Admin!"
        except DataValidationException as exc:
            print(f"  [PASS] Last Admin removal cleanly blocked: {exc.detail}")

        # -------------------------------------------------------------
        # 8. Test Non-Admin cannot remove members (403 Forbidden)
        # -------------------------------------------------------------
        print("\n[STEP 8] Testing Non-Admin permission enforcement...")
        from app.middleware.auth_middleware import require_admin_user

        try:
            # Ben is an employee in Company B
            require_admin_user(current_user=ben)
            assert False, "Non-admin user should not pass require_admin_user!"
        except PermissionDeniedException as exc:
            print(f"  [PASS] Non-admin access rejected with 403: {exc.detail}")

        # -------------------------------------------------------------
        # 9. Test Cross-Tenant Member Removal Isolation
        # -------------------------------------------------------------
        print("\n[STEP 9] Testing Cross-Tenant removal prevention (Bob trying to remove Alice)...")
        try:
            company_service_b.remove_team_member(user_id=alice.id, current_admin=bob)
            assert False, "Company B admin should NOT be able to remove Company A member!"
        except ResourceNotFoundException:
            print("  [PASS] Company B admin cannot access or remove Company A member (404 Scoped).")

        # -------------------------------------------------------------
        # 10. Test Company Shared Business Data Remains Intact
        # -------------------------------------------------------------
        print("\n[STEP 10] Verifying shared business data integrity after member removals...")
        kpi_count = db.query(KPIDefinition).filter(KPIDefinition.company_id == company_a_id).count()
        assert kpi_count == 1, "Company KPIs must remain untouched"
        print(f"  [PASS] Company A's shared KPIs remain intact (KPI Count = {kpi_count}).")

        print("\n" + "=" * 80)
        print("  ALL 10 REMOVE MEMBER LIFECYCLE & SECURITY TESTS PASSED! 100% VERIFIED")
        print("=" * 80)

    finally:
        db.close()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass


if __name__ == "__main__":
    run_remove_member_tests()
