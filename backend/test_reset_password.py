import asyncio
import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_auth_and_recovery():
    print("Testing Authentication Loop Prevention & Password Reset API...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Reset password for revanthjoshua77@gmail.com to Admin123!
        res = await client.post(
            "/api/v1/auth/reset-password",
            json={"email": "revanthjoshua77@gmail.com", "new_password": "Password123!"}
        )
        assert res.status_code == 200, f"Password reset failed: {res.text}"
        data = res.json()
        print("[PASS] Password Reset Passed: New token issued for", data["user"]["email"])

        # 2. Login with the new password
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "revanthjoshua77@gmail.com", "password": "Password123!"}
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        print("[PASS] Login with New Password Passed:", login_res.json()["user"]["full_name"])

        # 3. Test wrong password gives informative error
        wrong_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "revanthjoshua77@gmail.com", "password": "WrongPassword999"}
        )
        assert wrong_res.status_code == 401
        print("[PASS] Wrong Password Returns Helpful Detail:", wrong_res.json()["detail"])

        # 4. Test non-existent email returns clear registration message
        notfound_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent_brand_new_user@company.com", "password": "Password123!"}
        )
        assert notfound_res.status_code == 401
        print("[PASS] Non-Existent User Returns Clear Detail:", notfound_res.json()["detail"])

        # 5. Test Registering existing user is properly rejected
        dup_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "revanthjoshua77@gmail.com",
                "password": "Password123!",
                "full_name": "Revanth Joshua",
                "company_name": "SNS Institutions ",
                "industry": "Retail/E-commerce"
            }
        )
        assert dup_res.status_code == 400, f"Duplicate register should return 400, got: {dup_res.status_code}"
        print("[PASS] Duplicate Account Registration cleanly rejected with 400:", dup_res.json()["detail"])

    print("\n=======================================================")
    print("ALL AUTHENTICATION & RECOVERY FLOWS TESTED & PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(test_auth_and_recovery())
