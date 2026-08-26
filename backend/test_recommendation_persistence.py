from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_recommendation_persistence():
    print("Testing Recommendation Status Persistence in Database...")

    # 1. Login/Register
    auth_res = client.post("/api/v1/auth/login", json={"email": "revanth@sns.edu", "password": "password123"})
    if auth_res.status_code != 200:
        auth_res = client.post("/api/v1/auth/register", json={
            "email": "revanth@sns.edu",
            "password": "password123",
            "full_name": "Revanth Joshua R",
            "company_name": "SNS Institutions",
            "industry": "Restaurant & Food Service"
        })
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get or generate recommendations
    recs_res = client.get("/api/v1/recommendations", headers=headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    if not recs:
        client.post("/api/v1/recommendations/generate", headers=headers)
        recs = client.get("/api/v1/recommendations", headers=headers).json()

    assert len(recs) > 0, "Expected recommendations to exist"
    target_rec = recs[0]
    target_id = target_rec["id"]

    # 3. Mark in_progress
    upd1 = client.post(f"/api/v1/recommendations/{target_id}/status?status=in_progress", headers=headers)
    assert upd1.status_code == 200
    assert upd1.json()["status"] == "in_progress"

    # 4. Fetch list and confirm persisted status
    recs_check1 = client.get("/api/v1/recommendations", headers=headers).json()
    matching1 = next(r for r in recs_check1 if r["id"] == target_id)
    assert matching1["status"] == "in_progress", "Status in_progress did not persist!"

    # 5. Mark completed
    upd2 = client.post(f"/api/v1/recommendations/{target_id}/status?status=completed", headers=headers)
    assert upd2.status_code == 200
    assert upd2.json()["status"] == "completed"

    # 6. Fetch list and confirm persisted completed status
    recs_check2 = client.get("/api/v1/recommendations", headers=headers).json()
    matching2 = next(r for r in recs_check2 if r["id"] == target_id)
    assert matching2["status"] == "completed", "Status completed did not persist!"

    print(f"[PASS] Recommendation #{target_id} status transitions persisted successfully in SQLite!")

if __name__ == "__main__":
    test_recommendation_persistence()
