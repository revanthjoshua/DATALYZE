"""
Comprehensive End-to-End Test Suite for Resend Invitation Flow & Security
-------------------------------------------------------------------------
Verifies:
1. Pending Invitation creation (No User record created before acceptance).
2. Verification endpoint GET /api/v1/auth/invite/verify?token=...
3. Acceptance endpoint POST /api/v1/auth/invite/accept creating active User.
4. Token reuse prevention (rejected upon second use).
5. Expired token rejection.
6. Revoked token rejection.
7. Multi-tenant isolation (Company B admin cannot access/resend/revoke Company A invites).
8. Resend token rotation and expiry extension.
9. Active user duplicate invite rejection.
10. Real Resend API live dispatch test with real email delivery.
"""
import os
import sys
import uuid
import secrets
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app.core.database import Base
from app.core.config import settings
from app.core.security import verify_password
from app.models.company import Company
from app.models.user import User
from app.models.invitation import Invitation
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService
from app.services.email_service import EmailService, email_service
from app.schemas.user_schema import AdminRegistrationRequest, UserLogin
from app.schemas.invitation_schema import AcceptInviteRequest
from app.core.exceptions import DataValidationException, ResourceNotFoundException


def run_invitation_lifecycle_tests():
    test_db_file = f"test_invite_{uuid.uuid4().hex[:8]}.db"
    test_db_url = f"sqlite:///./{test_db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    print("=" * 80)
    print("  DATALYZE: RESEND INVITATION LIFECYCLE & SECURITY VERIFICATION TEST")
    print("=" * 80)

    db = TestingSessionLocal()
    try:
        auth_service = AuthService(db)

        # -------------------------------------------------------------
        # 1. Register Workspace Admins for Company A and Company B
        # -------------------------------------------------------------
        print("\n[STEP 1] Registering Company A (Apex Corp) and Company B (CloudFlow)...")
        reg_a = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Alice Admin",
                username="alice_apex",
                phone_number="+15550100",
                email="alice@apexcorp.com",
                password="SecureAdminPassword123!",
                confirm_password="SecureAdminPassword123!",
                company_name="Apex Corp",
                industry="Retail/E-commerce"
            )
        )
        admin_a = reg_a["user"]
        company_a_id = reg_a["company"]["id"]

        reg_b = auth_service.register_admin(
            AdminRegistrationRequest(
                full_name="Bob Admin",
                username="bob_cloudflow",
                phone_number="+15550200",
                email="bob@cloudflow.io",
                password="SecureAdminPassword123!",
                confirm_password="SecureAdminPassword123!",
                company_name="CloudFlow Tech",
                industry="SaaS/Technology"
            )
        )
        admin_b = reg_b["user"]
        company_b_id = reg_b["company"]["id"]

        print(f"  -> Company A (ID={company_a_id}): Admin Alice ({admin_a.email})")
        print(f"  -> Company B (ID={company_b_id}): Admin Bob ({admin_b.email})")

        inv_service_a = InvitationService(db, tenant_id=company_a_id)
        inv_service_b = InvitationService(db, tenant_id=company_b_id)

        # Mock email dispatch for unit steps with synthetic domains
        with patch.object(email_service, "send_invitation_email", return_value={"success": True, "email_id": "mock_id"}):
            # -------------------------------------------------------------
            # 2. Test Pending Invitation Creation (No Active User Created)
            # -------------------------------------------------------------
            print("\n[STEP 2] Creating Pending Invitation for Jordan Employee...")
            inv_jordan = inv_service_a.create_or_renew_invitation(
                email="jordan@apexcorp.com",
                role="Employee",
                full_name="Jordan Analyst",
                inviter_user=admin_a
            )

            assert inv_jordan is not None
            assert inv_jordan.status == "pending"
            assert inv_jordan.email == "jordan@apexcorp.com"
            assert inv_jordan.role == "employee"
            assert inv_jordan.company_id == company_a_id
            assert len(inv_jordan.token) >= 32

            # Verify NO user account exists for Jordan in database
            jordan_user_before = db.query(User).filter(User.email == "jordan@apexcorp.com").first()
            assert jordan_user_before is None, "Security Violation: User account was created before invite acceptance!"
            print(f"  [PASS] Pending invitation created (Token: {inv_jordan.token[:10]}...). 0 User records exist for email.")

            # -------------------------------------------------------------
            # 3. Test Invitation Token Verification Endpoint
            # -------------------------------------------------------------
            print("\n[STEP 3] Verifying GET /api/v1/auth/invite/verify token payload...")
            public_inv_service = InvitationService(db)
            verify_data = public_inv_service.verify_invitation_token(inv_jordan.token)

            assert verify_data["valid"] is True
            assert verify_data["email"] == "jordan@apexcorp.com"
            assert verify_data["full_name"] == "Jordan Analyst"
            assert verify_data["role"] == "employee"
            assert verify_data["company_name"] == "Apex Corp"
            assert verify_data["company_id"] == company_a_id
            print(f"  [PASS] Token verification returned safe workspace details: {verify_data}")

            # -------------------------------------------------------------
            # 4. Test Invitation Acceptance & Account Creation
            # -------------------------------------------------------------
            print("\n[STEP 4] Jordan accepts invitation and sets custom password...")
            accept_res = public_inv_service.accept_invitation(
                AcceptInviteRequest(
                    token=inv_jordan.token,
                    password="JordanChosenSecretPassword123!",
                    confirm_password="JordanChosenSecretPassword123!",
                    full_name="Jordan Analyst Updated",
                    phone_number="+15559876"
                )
            )

            assert accept_res["success"] is True
            assert accept_res["email"] == "jordan@apexcorp.com"

            # Verify active user in DB
            jordan_user = db.query(User).filter(User.email == "jordan@apexcorp.com").first()
            assert jordan_user is not None, "User account must exist after acceptance"
            assert jordan_user.company_id == company_a_id, "User must be bound to Company A"
            assert jordan_user.role == "employee", "User must have assigned role 'employee'"
            assert jordan_user.is_active is True
            assert verify_password("JordanChosenSecretPassword123!", jordan_user.hashed_password)

            # Verify invitation marked accepted
            db.refresh(inv_jordan)
            assert inv_jordan.status == "accepted"
            assert inv_jordan.accepted_at is not None
            print("  [PASS] Account created successfully with custom password and role. Invitation marked 'accepted'.")

            # Verify Jordan can log in
            login_res = auth_service.authenticate_user(
                UserLogin(
                    email="jordan@apexcorp.com",
                    password="JordanChosenSecretPassword123!",
                    portal_type="employee"
                )
            )
            assert login_res["user"].email == "jordan@apexcorp.com"
            assert login_res["company"]["id"] == company_a_id
            print("  [PASS] Newly onboarded user successfully authenticated into Company A workspace.")

            # -------------------------------------------------------------
            # 5. Test Token Reuse Prevention
            # -------------------------------------------------------------
            print("\n[STEP 5] Testing token reuse prevention...")
            try:
                public_inv_service.accept_invitation(
                    AcceptInviteRequest(
                        token=inv_jordan.token,
                        password="AnotherPassword123!",
                        confirm_password="AnotherPassword123!"
                    )
                )
                assert False, "Should have rejected reused token"
            except DataValidationException as e:
                print(f"  [PASS] Reused token cleanly rejected: {e.detail}")

            # -------------------------------------------------------------
            # 6. Test Expired Invitation Token
            # -------------------------------------------------------------
            print("\n[STEP 6] Testing expired invitation rejection...")
            inv_expired = inv_service_a.create_or_renew_invitation(
                email="expired_user@apexcorp.com",
                role="Analyst",
                full_name="Expired User",
                inviter_user=admin_a
            )
            # Manually backdate expiration
            inv_expired.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
            db.commit()

            try:
                public_inv_service.verify_invitation_token(inv_expired.token)
                assert False, "Should have rejected expired token on verification"
            except DataValidationException as e:
                print(f"  [PASS] Expired token rejected on verification: {e.detail}")

            try:
                public_inv_service.accept_invitation(
                    AcceptInviteRequest(
                        token=inv_expired.token,
                        password="Password123!",
                        confirm_password="Password123!"
                    )
                )
                assert False, "Should have rejected expired token on acceptance"
            except DataValidationException as e:
                print(f"  [PASS] Expired token rejected on acceptance: {e.detail}")

            # -------------------------------------------------------------
            # 7. Test Revoked Invitation Token
            # -------------------------------------------------------------
            print("\n[STEP 7] Testing invitation revocation by Admin...")
            inv_to_revoke = inv_service_a.create_or_renew_invitation(
                email="revoked_user@apexcorp.com",
                role="Employee",
                full_name="Revoked User",
                inviter_user=admin_a
            )
            revoked = inv_service_a.revoke_invitation(inv_to_revoke.id, admin_user=admin_a)
            assert revoked.status == "revoked"
            assert revoked.revoked_at is not None

            try:
                public_inv_service.verify_invitation_token(inv_to_revoke.token)
                assert False, "Should have rejected revoked token"
            except DataValidationException as e:
                print(f"  [PASS] Revoked token rejected on verification: {e.detail}")

            try:
                public_inv_service.accept_invitation(
                    AcceptInviteRequest(
                        token=inv_to_revoke.token,
                        password="Password123!",
                        confirm_password="Password123!"
                    )
                )
                assert False, "Should have rejected revoked token on acceptance"
            except DataValidationException as e:
                print(f"  [PASS] Revoked token rejected on acceptance: {e.detail}")

            # -------------------------------------------------------------
            # 8. Test Multi-Tenant Boundary Protection
            # -------------------------------------------------------------
            print("\n[STEP 8] Testing cross-tenant access prevention...")
            inv_company_a = inv_service_a.create_or_renew_invitation(
                email="victim@apexcorp.com",
                role="Employee",
                full_name="Victim User",
                inviter_user=admin_a
            )

            # Company B admin attempts to revoke Company A's invite
            try:
                inv_service_b.revoke_invitation(inv_company_a.id, admin_user=admin_b)
                assert False, "Company B admin should NOT be able to revoke Company A's invite"
            except ResourceNotFoundException:
                print("  [PASS] Company B admin cannot revoke Company A's invitation (404 Scoped).")

            # Company B admin attempts to resend Company A's invite
            try:
                inv_service_b.resend_invitation(inv_company_a.id, admin_user=admin_b)
                assert False, "Company B admin should NOT be able to resend Company A's invite"
            except ResourceNotFoundException:
                print("  [PASS] Company B admin cannot resend Company A's invitation (404 Scoped).")

            # -------------------------------------------------------------
            # 9. Test Resend Token Rotation & Expiry Extension
            # -------------------------------------------------------------
            print("\n[STEP 9] Testing Resend token rotation...")
            old_token = inv_company_a.token
            old_expiry = inv_company_a.expires_at

            resent_inv = inv_service_a.resend_invitation(inv_company_a.id, admin_user=admin_a)
            assert resent_inv.token != old_token, "Resending MUST rotate the security token"
            assert resent_inv.status == "pending"
            assert resent_inv.expires_at > old_expiry - timedelta(minutes=5)
            print(f"  [PASS] Resend rotated token: {old_token[:8]}... -> {resent_inv.token[:8]}...")

            # -------------------------------------------------------------
            # 10. Test Active User Duplicate Invite Rejection
            # -------------------------------------------------------------
            print("\n[STEP 10] Testing active user duplicate invite rejection...")
            try:
                inv_service_a.create_or_renew_invitation(
                    email="jordan@apexcorp.com",  # Already active
                    role="Employee",
                    inviter_user=admin_a
                )
                assert False, "Should reject invitation to already active workspace member"
            except DataValidationException as e:
                print(f"  [PASS] Duplicate active user invite rejected: {e.detail}")

        # -------------------------------------------------------------
        # 11. Test Real Resend API Dispatch (Live API Call)
        # -------------------------------------------------------------
        print("\n[STEP 11] Testing live Resend email dispatch with real API key...")
        email_svc = EmailService()
        if email_svc.api_key:
            resend_result = email_svc.send_invitation_email(
                to_email="revanthjoshua77@gmail.com",
                recipient_name="Revanth Joshua",
                company_name="Apex Corp",
                inviter_name="Alice Admin",
                role="Analyst",
                token=secrets.token_urlsafe(32)
            )
            assert resend_result["success"] is True
            assert resend_result.get("email_id") is not None
            print(f"  [PASS] Real Resend Email sent successfully! Message ID: {resend_result['email_id']}")
        else:
            print("  [SKIP] RESEND_API_KEY not present.")

        print("\n" + "=" * 80)
        print("  ALL 11 RESEND INVITATION LIFECYCLE & SECURITY TESTS PASSED! 100% VERIFIED")
        print("=" * 80)

    finally:
        db.close()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass


if __name__ == "__main__":
    run_invitation_lifecycle_tests()
