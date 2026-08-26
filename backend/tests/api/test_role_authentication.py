import pytest


def test_admin_and_employee_role_authentication_separation(client):
    # Setup: Explicitly register test Admin and Employee accounts
    client.post("/api/v1/auth/register-admin", json={
        "full_name": "Admin Leader",
        "phone_number": "+15550100",
        "email": "admin@datalyze.com",
        "username": "admin",
        "password": "Admin123!",
        "confirm_password": "Admin123!",
        "company_name": "Acme Global Workspace",
        "industry": "Retail/E-commerce"
    })

    client.post("/api/v1/auth/register-employee", json={
        "full_name": "Jordan Reed",
        "phone_number": "+15550199",
        "email": "employee@datalyze.com",
        "username": "employee",
        "password": "Employee123!",
        "confirm_password": "Employee123!"
    })

    # 1. Test Admin Login with Email
    admin_res = client.post("/api/v1/auth/login", json={
        "email": "admin@datalyze.com",
        "password": "Admin123!",
        "portal_type": "admin"
    })
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert "access_token" in admin_data
    assert admin_data["user"]["role"] in ["Company Admin", "admin"]

    # 2. Test Admin Login with Username
    admin_u_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin",
        "password": "Admin123!",
        "portal_type": "admin"
    })
    assert admin_u_res.status_code == 200
    assert admin_u_res.json()["user"]["email"] == "admin@datalyze.com"

    # 3. Test Employee Login with Email
    emp_res = client.post("/api/v1/auth/login", json={
        "email": "employee@datalyze.com",
        "password": "Employee123!",
        "portal_type": "employee"
    })
    assert emp_res.status_code == 200
    emp_data = emp_res.json()
    assert "access_token" in emp_data
    assert emp_data["user"]["role"] in ["Employee", "employee"]

    # 4. Test Employee Login with Username
    emp_u_res = client.post("/api/v1/auth/login", json={
        "identifier": "employee",
        "password": "Employee123!",
        "portal_type": "employee"
    })
    assert emp_u_res.status_code == 200
    assert emp_u_res.json()["user"]["email"] == "employee@datalyze.com"

    # 5. Security: Employee trying to log in via Admin Portal (403 Forbidden)
    denied_res = client.post("/api/v1/auth/login", json={
        "identifier": "employee@datalyze.com",
        "password": "Employee123!",
        "portal_type": "admin"
    })
    assert denied_res.status_code == 403
    assert "restricted to Company Administrators" in denied_res.json()["detail"]

    # 6. Security: Admin trying to log in via Employee Portal (403 Forbidden)
    admin_on_emp = client.post("/api/v1/auth/login", json={
        "identifier": "admin@datalyze.com",
        "password": "Admin123!",
        "portal_type": "employee"
    })
    assert admin_on_emp.status_code == 403
    assert "Administrator accounts must sign in via the Admin Portal" in admin_on_emp.json()["detail"]

    # 7. Test Invalid Password
    bad_pw_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin",
        "password": "WrongPassword123!",
        "portal_type": "admin"
    })
    assert bad_pw_res.status_code == 401

    # 8. Test Non-existent User
    no_user_res = client.post("/api/v1/auth/login", json={
        "identifier": "unknown_user_999",
        "password": "Password123!",
        "portal_type": "employee"
    })
    assert no_user_res.status_code == 401


def test_admin_and_employee_registration_and_password_reset(client):
    # 1. Register new Admin with Full Name, Phone, Email, Username, Password
    new_admin_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Sarah Connor (Admin)",
        "phone_number": "+1555123456",
        "email": "sarah.admin@datalyze.com",
        "username": "sarah_admin",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "company_name": "Cyberdyne Systems",
        "industry": "SaaS / B2B"
    })
    assert new_admin_res.status_code == 201
    assert new_admin_res.json()["user"]["username"] == "sarah_admin"
    assert new_admin_res.json()["user"]["role"] in ["Company Admin", "admin"]

    # Test Duplicate Username rejection
    dup_res = client.post("/api/v1/auth/register-admin", json={
        "full_name": "Duplicate Sarah",
        "phone_number": "+1555123499",
        "email": "other.email@datalyze.com",
        "username": "sarah_admin",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!"
    })
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"]

    # 2. Register new Employee with Full Name, Phone, Email, Username, Password
    new_emp_res = client.post("/api/v1/auth/register-employee", json={
        "full_name": "Kyle Reese (Staff)",
        "phone_number": "+1555987654",
        "email": "kyle.reese@datalyze.com",
        "username": "kyle_reese",
        "password": "EmployeeSecret123!",
        "confirm_password": "EmployeeSecret123!"
    })
    assert new_emp_res.status_code == 201
    assert new_emp_res.json()["user"]["username"] == "kyle_reese"
    assert new_emp_res.json()["user"]["role"] in ["Employee", "employee"]

    # 3. Test Full Forgot Password Flow for Employee
    # Step A: Request code with email
    req_res = client.post("/api/v1/auth/forgot-password/request", json={
        "identifier": "kyle.reese@datalyze.com",
        "portal_type": "employee"
    })
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["success"] is True
    code = req_data["code_preview"]
    assert len(code) == 6

    # Step B: Verify code
    verify_res = client.post("/api/v1/auth/forgot-password/verify", json={
        "identifier": "kyle.reese@datalyze.com",
        "code": code,
        "portal_type": "employee"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # Step C: Confirm new password
    confirm_res = client.post("/api/v1/auth/forgot-password/confirm", json={
        "identifier": "kyle.reese@datalyze.com",
        "code": code,
        "new_password": "BrandNewPassword123!",
        "confirm_password": "BrandNewPassword123!",
        "portal_type": "employee"
    })
    assert confirm_res.status_code == 200
    assert confirm_res.json()["success"] is True

    # Step D: Sign in with the new password
    login_new_pw = client.post("/api/v1/auth/login", json={
        "identifier": "kyle_reese",
        "password": "BrandNewPassword123!",
        "portal_type": "employee"
    })
    assert login_new_pw.status_code == 200
    assert login_new_pw.json()["user"]["username"] == "kyle_reese"

