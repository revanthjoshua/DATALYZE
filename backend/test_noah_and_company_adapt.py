import sys
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.company import Company
from app.models.user import User
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def test_noah_and_company_adapt():
    print("Testing Company Settings Auto-Adaptation and Noah Intelligence...")
    
    # 1. Login
    db = SessionLocal()
    user = db.query(User).filter(User.email == "demo@datalyze.ai").first()
    if not user:
        company = Company(name="Test Auto Company", industry="Universal Services", currency="USD", timezone="UTC")
        db.add(company)
        db.commit()
        db.refresh(company)
        user = User(email="demo@datalyze.ai", hashed_password=hash_password("DemoPass123!"), full_name="Alex Rivera", role="admin", company_id=company.id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = create_access_token({"sub": str(user.id), "company_id": user.company_id, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Ingest Sample Restaurant Data
    sample_csv = "date,dish_name,food_category,dining_type,prep_time_min,price_inr,quantity,discount_inr,customer_rating\n"
    for i in range(1, 20):
        sample_csv += f"2026-08-{i:02d},Hyderabadi Biryani,Main Course,Dine-in,25,350,10,20,4.8\n"
        sample_csv += f"2026-08-{i:02d},Paneer Butter Masala,Main Course,Delivery,18,280,15,15,4.6\n"
    
    files = {"file": ("royal_spice_restaurant_orders.csv", sample_csv, "text/csv")}
    ingest_res = client.post("/api/v1/data/upload", files=files, headers=headers)
    assert ingest_res.status_code == 200, f"Ingest failed: {ingest_res.text}"
    print("[PASS] Ingested restaurant CSV successfully")
    
    # 3. Check Detected Profile
    det_res = client.get("/api/v1/company/detected-profile", headers=headers)
    assert det_res.status_code == 200, f"Detected profile failed: {det_res.text}"
    profile = det_res.json()
    print(f"[PASS] Detected Profile: Industry={profile.get('industry')}, Currency={profile.get('currency')}, Name={profile.get('company_name')}")
    assert "Restaurant" in profile.get("industry"), "Expected Restaurant industry detected"
    assert profile.get("currency") == "INR", "Expected INR currency detected"
    
    # 4. Check Auto-Adapt Endpoint
    adapt_res = client.post("/api/v1/company/auto-adapt", headers=headers)
    assert adapt_res.status_code == 200, f"Auto adapt failed: {adapt_res.text}"
    updated_company = adapt_res.json()
    print(f"[PASS] Auto-Adapted Company: {updated_company['name']}, {updated_company['industry']}, {updated_company['currency']}")
    
    # 5. Test Noah Web & Technology Knowledge
    web_queries = [
        "What is React?",
        "What is an API?",
        "What is DNS?",
        "What is Docker?",
        "What is WebSocket?"
    ]
    for q in web_queries:
        res = client.post("/api/v1/noah/query", json={"question": q}, headers=headers)
        assert res.status_code == 200, f"Noah query failed: {res.text}"
        ans = res.json()["answer"]
        assert len(ans) > 20, f"Empty answer for {q}"
        assert "#" not in ans and "*" not in ans, "Markdown symbols should be stripped"
        print(f"[PASS] Noah answered Web Query '{q}': {ans[:70]}...")

    # 6. Test Noah Data-Grounded Query
    data_res = client.post("/api/v1/noah/query", json={"question": "What is our total price inr and average prep time?"}, headers=headers)
    assert data_res.status_code == 200
    data_ans = data_res.json()["answer"]
    print(f"[PASS] Noah Data Query: {data_ans[:100]}...")
    
    # 7. Test Noah Missing Metric Query (Should not hallucinate)
    missing_res = client.post("/api/v1/noah/query", json={"question": "What is our employee hospital insurance cost?"}, headers=headers)
    assert missing_res.status_code == 200
    missing_ans = missing_res.json()["answer"]
    print(f"[PASS] Noah Missing Column Query: {missing_ans[:100]}...")
    assert "couldn't find" in missing_ans.lower() or "columns" in missing_ans.lower(), "Noah should report column unavailability instead of hallucinating"

    print("\n=======================================================")
    print("ALL NOAH & COMPANY ADAPTATION TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_noah_and_company_adapt()
