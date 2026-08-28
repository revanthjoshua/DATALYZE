import pytest
import time
from app.models.user import User
from app.models.company import Company
from app.core.security import create_access_token


def test_employee_registration_on_zero_admin_fresh_db_is_safely_rejected(db_session, client):
    """
    SECURITY REGRESSION TEST:
    When 0 Admin accounts and 0 Company workspaces exist:
    Employee registration MUST FAIL with 400 Bad Request.
    Must NOT create admin@datalyze.com, Admin123!, Acme Global Workspace, or any default admin.
    """
    # Verify no users or companies exist
    db_session.query(User).delete()
    db_session.query(Company).delete()
    db_session.commit()

    res = client.post("/api/v1/auth/register-employee", json={
        "full_name": "Lone Employee",
        "phone_number": "+1555123999",
        "email": "employee@orphan.com",
        "username": "orphan_emp",
        "password": "SecretPassword123!",
        "confirm_password": "SecretPassword123!",
        "company_name": "Nonexistent Corp"
    })

    assert res.status_code == 400
    err_msg = res.json()["detail"]
    assert "Direct employee registration is not permitted" in err_msg or "invitation" in err_msg.lower()

    # Verify no admin account was auto-created in database
    admin_user = db_session.query(User).filter(User.email == "admin@datalyze.com").first()
    assert admin_user is None, "Security Violation: admin@datalyze.com was auto-created!"

    # Verify no fake company was auto-created
    fake_comp = db_session.query(Company).filter(Company.name == "Acme Global Workspace").first()
    assert fake_comp is None, "Security Violation: Default 'Acme Global Workspace' was auto-created!"

    # Verify zero users exist
    total_users = db_session.query(User).count()
    assert total_users == 0, f"Expected 0 users, found {total_users}"


def test_admin_registration_creates_workspace_and_admin(client):
    """
    Verifies that company creation and admin provisioning is an explicit Admin responsibility.
    """
    suffix = str(int(time.time()))
    res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Alice Admin",
        "phone_number": f"+1555{suffix[-4:]}1",
        "email": f"alice_{suffix}@alphaenterprise.com",
        "username": f"alice_admin_{suffix}",
        "password": "AlphaAdminPassword123!",
        "confirm_password": "AlphaAdminPassword123!",
        "company_name": f"Alpha Enterprise {suffix}",
        "industry": "Retail/E-commerce"
    })

    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] in ["Company Admin", "company_admin", "admin"]
    assert data["company"]["name"] == f"Alpha Enterprise {suffix}"


def test_employee_registration_joins_legitimate_workspace(client):
    """
    Verifies that an Employee can legitimately join an existing workspace via invitation token.
    """
    suffix = str(int(time.time()))
    comp_name = f"Beta Technologies {suffix}"
    
    # 1. Admin creates Beta Technologies
    adm_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Bob Admin",
        "phone_number": f"+1555{suffix[-4:]}2",
        "email": f"bob_{suffix}@betatech.com",
        "username": f"bob_admin_{suffix}",
        "password": "BetaAdminPassword123!",
        "confirm_password": "BetaAdminPassword123!",
        "company_name": comp_name,
        "industry": "SaaS / B2B"
    })
    admin_token = adm_res.json()["access_token"]

    # Admin invites Charlie
    inv_res = client.post("/api/v1/company/invite", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "email": f"charlie_{suffix}@betatech.com",
        "recipient_name": "Charlie Employee",
        "role": "employee"
    })
    assert inv_res.status_code == 201
    invite_token = inv_res.json()["token"]

    # 2. Employee joins Beta Technologies via invitation token
    emp_res = client.post("/api/v1/auth/register-employee", json={
        "full_name": "Charlie Employee",
        "phone_number": f"+1555{suffix[-4:]}3",
        "email": f"charlie_{suffix}@betatech.com",
        "username": f"charlie_emp_{suffix}",
        "invitation_token": invite_token,
        "password": "CharliePassword123!",
        "confirm_password": "CharliePassword123!"
    })

    assert emp_res.status_code == 201
    emp_data = emp_res.json()
    assert emp_data["user"]["role"] in ["Employee", "employee"]
    assert emp_data["company"]["name"] == comp_name


def test_employee_registration_rejects_nonexistent_workspace(client):
    """
    Verifies that employee attempting direct registration without invitation is rejected.
    """
    suffix = str(int(time.time()))
    res = client.post("/api/v1/auth/register-employee", json={
        "full_name": "Dan Worker",
        "phone_number": f"+1555{suffix[-4:]}4",
        "email": f"dan_{suffix}@fakecompany999.com",
        "username": f"dan_worker_{suffix}",
        "company_name": "Totally Nonexistent Company XYZ 999",
        "password": "DanPassword123!",
        "confirm_password": "DanPassword123!"
    })

    assert res.status_code == 400
    assert "Direct employee registration is not permitted" in res.json()["detail"] or "invitation" in res.json()["detail"].lower()


def test_duplicate_email_and_username_rejections(client):
    """
    Verifies that duplicate registrations (email or username) are strictly rejected with 400.
    """
    suffix = str(int(time.time()))
    email = f"dup_{suffix}@gammainc.com"
    username = f"gamma_user_{suffix}"

    # First registration
    res1 = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Gamma Admin",
        "phone_number": f"+1555{suffix[-4:]}5",
        "email": email,
        "username": username,
        "password": "GammaPassword123!",
        "confirm_password": "GammaPassword123!",
        "company_name": f"Gamma Inc {suffix}"
    })
    assert res1.status_code == 201

    # Duplicate email
    res_dup_email = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Gamma Imposter",
        "phone_number": f"+1555{suffix[-4:]}6",
        "email": email,
        "username": f"diff_user_{suffix}",
        "password": "GammaPassword123!",
        "confirm_password": "GammaPassword123!",
        "company_name": f"Gamma Fake {suffix}"
    })
    assert res_dup_email.status_code == 400
    assert "already exists" in res_dup_email.json()["detail"]

    # Duplicate username
    res_dup_user = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Gamma Imposter 2",
        "phone_number": f"+1555{suffix[-4:]}7",
        "email": f"other_{suffix}@gammainc.com",
        "username": username,
        "password": "GammaPassword123!",
        "confirm_password": "GammaPassword123!",
        "company_name": f"Gamma Fake 2 {suffix}"
    })
    assert res_dup_user.status_code == 400
    assert "already taken" in res_dup_user.json()["detail"]


def test_cross_role_login_portal_segregation(client):
    """
    Verifies strict portal role separation:
    - Employee attempting Admin login -> 403 Forbidden
    - Admin attempting Employee login -> 403 Forbidden
    """
    suffix = str(int(time.time()))
    comp_name = f"Delta Global {suffix}"

    # Register Admin
    adm_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Delta Admin",
        "phone_number": f"+1555{suffix[-4:]}8",
        "email": f"admin_{suffix}@deltaglobal.com",
        "username": f"delta_admin_{suffix}",
        "password": "DeltaPassword123!",
        "confirm_password": "DeltaPassword123!",
        "company_name": comp_name
    })
    admin_token = adm_res.json()["access_token"]

    # Admin invites Staff
    inv_res = client.post("/api/v1/company/invite", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "email": f"staff_{suffix}@deltaglobal.com",
        "recipient_name": "Delta Staff",
        "role": "employee"
    })
    invite_token = inv_res.json()["token"]

    # Register Employee
    client.post("/api/v1/auth/register-employee", json={
        "full_name": "Delta Staff",
        "phone_number": f"+1555{suffix[-4:]}9",
        "email": f"staff_{suffix}@deltaglobal.com",
        "username": f"delta_staff_{suffix}",
        "invitation_token": invite_token,
        "password": "StaffPassword123!",
        "confirm_password": "StaffPassword123!"
    })

    # 1. Employee tries Admin portal -> MUST BE 403
    emp_on_admin = client.post("/api/v1/auth/login", json={
        "identifier": f"delta_staff_{suffix}",
        "password": "StaffPassword123!",
        "portal_type": "admin"
    })
    assert emp_on_admin.status_code == 403
    assert "restricted to Company Administrators" in emp_on_admin.json()["detail"]

    # 2. Admin tries Employee portal -> MUST BE 403
    admin_on_emp = client.post("/api/v1/auth/login", json={
        "identifier": f"delta_admin_{suffix}",
        "password": "DeltaPassword123!",
        "portal_type": "employee"
    })
    assert admin_on_emp.status_code == 403
    assert "Administrator accounts must sign in via the Admin Portal" in admin_on_emp.json()["detail"]


def test_authentication_token_security_and_missing_token(client):
    """
    Verifies protected API endpoints enforce 401 on missing or forged tokens.
    """
    # 1. Missing Token -> 401
    no_token_res = client.get("/api/v1/auth/me")
    assert no_token_res.status_code == 401
    assert "token is missing" in no_token_res.json()["detail"].lower()

    # 2. Forged / Invalid Token -> 401
    bad_token_res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer forged.invalid.token.12345"})
    assert bad_token_res.status_code == 401


def test_employee_rbac_admin_endpoint_restriction(client):
    """
    Verifies that an Employee user cannot access Admin-only endpoints (403 Forbidden).
    """
    suffix = str(int(time.time()))
    comp_name = f"Epsilon Services {suffix}"

    # Register Admin & Employee
    adm_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Epsilon Admin",
        "phone_number": f"+1555{suffix[-4:]}1",
        "email": f"admin_{suffix}@epsilon.com",
        "username": f"eps_admin_{suffix}",
        "password": "EpsilonPass123!",
        "confirm_password": "EpsilonPass123!",
        "company_name": comp_name
    })
    admin_token = adm_res.json()["access_token"]

    inv_res = client.post("/api/v1/company/invite", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "email": f"staff_{suffix}@epsilon.com",
        "recipient_name": "Epsilon Staff",
        "role": "employee"
    })
    invite_token = inv_res.json()["token"]

    emp_res = client.post("/api/v1/auth/register-employee", json={
        "full_name": "Epsilon Staff",
        "phone_number": f"+1555{suffix[-4:]}2",
        "email": f"staff_{suffix}@epsilon.com",
        "username": f"eps_staff_{suffix}",
        "invitation_token": invite_token,
        "password": "StaffPassword123!",
        "confirm_password": "StaffPassword123!"
    })
    emp_token = emp_res.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Employee tries to update company workspace settings (Admin-only) -> 403 Forbidden
    comp_update = client.put("/api/v1/company", headers=emp_headers, json={
        "name": "Malicious Workspace Rename"
    })
    assert comp_update.status_code == 403
    assert "Admin privileges required" in comp_update.json()["detail"]


def test_tenant_isolation_boundary_between_companies(client):
    """
    Verifies that Tenant A cannot view or access Tenant B's data (0 data leakage).
    """
    suffix = str(int(time.time()))

    # Company 1
    reg1 = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Tenant One Admin",
        "phone_number": f"+1555{suffix[-4:]}3",
        "email": f"admin_{suffix}@tenantone.com",
        "username": f"t1_admin_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": f"Tenant One {suffix}"
    })
    token1 = reg1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Company 2
    reg2 = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Tenant Two Admin",
        "phone_number": f"+1555{suffix[-4:]}4",
        "email": f"admin_{suffix}@tenanttwo.com",
        "username": f"t2_admin_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": f"Tenant Two {suffix}"
    })
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Load data for Company 1
    client.post("/api/v1/data/load-sample", headers=headers1)
    kpis1 = client.get("/api/v1/kpis", headers=headers1).json()
    assert len(kpis1) > 0

    # Company 2 query -> MUST BE EMPTY
    kpis2 = client.get("/api/v1/kpis", headers=headers2).json()
    assert len(kpis2) == 0, f"Tenant leakage! Company 2 saw {len(kpis2)} KPIs from Company 1"


def test_password_reset_flow_with_old_password_invalidation(client):
    """
    Verifies complete 3-step Password Reset / OTP Lifecycle:
    Request OTP -> Verify OTP -> Confirm New Password -> Old Password Fails (401) -> New Password Succeeds (200).
    """
    suffix = str(int(time.time()))
    email = f"reset_user_{suffix}@securecorp.com"

    # Register Admin
    client.post("/api/v1/auth/register-admin", json={
        "full_name": "Reset Test User",
        "phone_number": f"+1555{suffix[-4:]}5",
        "email": email,
        "username": f"reset_user_{suffix}",
        "password": "OriginalPassword123!",
        "confirm_password": "OriginalPassword123!",
        "company_name": f"Secure Corp {suffix}"
    })

    # Step 1: Request OTP
    req = client.post("/api/v1/auth/forgot-password/request", json={
        "identifier": email,
        "portal_type": "admin"
    })
    assert req.status_code == 200
    assert "code_preview" not in req.json()
    from app.services.email_service import email_service
    otp = email_service.sent_otps.get(email, email_service.last_sent_otp)
    assert otp is not None
    assert len(otp) == 6

    # Step 2: Verify OTP
    ver = client.post("/api/v1/auth/forgot-password/verify", json={
        "identifier": email,
        "code": otp,
        "portal_type": "admin"
    })
    assert ver.status_code == 200
    assert ver.json()["valid"] is True

    # Step 3: Confirm new password
    conf = client.post("/api/v1/auth/forgot-password/confirm", json={
        "identifier": email,
        "code": otp,
        "new_password": "UpgradedStrongPassword2026!",
        "confirm_password": "UpgradedStrongPassword2026!",
        "portal_type": "admin"
    })
    assert conf.status_code == 200

    # Old password MUST fail with 401
    old_login = client.post("/api/v1/auth/login", json={
        "identifier": email,
        "password": "OriginalPassword123!",
        "portal_type": "admin"
    })
    assert old_login.status_code == 401

    # New password MUST succeed with 200
    new_login = client.post("/api/v1/auth/login", json={
        "identifier": email,
        "password": "UpgradedStrongPassword2026!",
        "portal_type": "admin"
    })
    assert new_login.status_code == 200


def test_agentic_noah_gated_and_conversational_noah_active(client):
    """
    Verifies that conversational Noah works while agentic reasoning is 403-gated.
    """
    suffix = str(int(time.time()))
    reg = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Noah Evaluator",
        "phone_number": f"+1555{suffix[-4:]}6",
        "email": f"noah_{suffix}@evaluator.com",
        "username": f"noah_eval_{suffix}",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "company_name": f"Noah Eval {suffix}"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Standard conversational query -> 200 OK
    q_res = client.post("/api/v1/noah/query", headers=headers, json={
        "question": "What are our critical business trends?"
    })
    assert q_res.status_code == 200
    assert "answer" in q_res.json()

    # Agentic reasoning -> 403 Forbidden
    ag_res = client.post("/api/v1/noah/agentic-reasoning", headers=headers, json={
        "goal": "Autonomous execution"
    })
    assert ag_res.status_code == 403
    assert "reserved for Phase 5" in ag_res.json()["detail"]


def test_rate_limiting_triggers_429_on_excessive_attempts():
    """
    Verifies that RateLimitMiddleware protects sensitive endpoints and triggers 429 when limits are exceeded.
    """
    from app.middleware.rate_limit_middleware import rate_limiter
    rate_limiter.reset()
    
    # Test rate limiter directly on auth login path
    test_ip = "192.168.1.99"
    test_path = "/api/v1/auth/login"
    
    # Send requests up to limit (40 requests in 60s)
    for _ in range(40):
        is_limited, _ = rate_limiter.is_rate_limited(test_ip, test_path)
        assert is_limited is False

    # 41st request MUST be rate limited
    is_limited, retry_after = rate_limiter.is_rate_limited(test_ip, test_path)
    assert is_limited is True
    assert retry_after > 0
    
    rate_limiter.reset()

