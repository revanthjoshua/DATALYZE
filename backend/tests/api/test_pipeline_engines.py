import pytest


def test_detection_prediction_recommendation_and_noah_pipeline(client):
    # 1. Register test tenant
    res = client.post("/api/v1/auth/register", json={
        "email": "pipeline_leader@intel.com",
        "password": "Password123!",
        "full_name": "Marcus Vance",
        "company_name": "Vance Retail Analytics",
        "industry": "Retail/E-commerce"
    })
    assert res.status_code == 201
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Load 30-day realistic sample dataset
    load_res = client.post("/api/v1/data/load-sample", headers=headers)
    assert load_res.status_code == 200

    # 3. Trigger Anomaly Detection Engine
    det_res = client.post("/api/v1/detections/run", headers=headers)
    assert det_res.status_code == 200
    detections = det_res.json()
    assert isinstance(detections, list)

    # 4. Trigger Prediction Engine
    pred_res = client.post("/api/v1/predictions/generate?horizon_days=7", headers=headers)
    assert pred_res.status_code == 200
    predictions = pred_res.json()
    assert len(predictions) > 0

    # Verify prediction contract: ALWAYS a range + confidence level
    first_pred = predictions[0]
    assert "predicted_value" in first_pred
    assert "range_low" in first_pred
    assert "range_high" in first_pred
    assert "confidence_level" in first_pred
    assert first_pred["range_low"] <= first_pred["predicted_value"] <= first_pred["range_high"]

    # 5. Trigger Recommendation Engine
    rec_res = client.post("/api/v1/recommendations/generate", headers=headers)
    assert rec_res.status_code == 200
    recommendations = rec_res.json()
    assert isinstance(recommendations, list)

    # 6. Query Noah: Ask about revenue
    noah_res = client.post("/api/v1/noah/query", headers=headers, json={
        "question": "What is our current revenue status and forecast for next week?"
    })
    assert noah_res.status_code == 200
    noah_data = noah_res.json()
    assert "answer" in noah_data
    assert len(noah_data["answer"]) > 10
    assert len(noah_data["suggested_actions"]) > 0

    # 7. Query Noah: Ask about root cause / anomalies
    noah_why_res = client.post("/api/v1/noah/query", headers=headers, json={
        "question": "Why did revenue drop in Region East?"
    })
    assert noah_why_res.status_code == 200
    assert len(noah_why_res.json()["answer"]) > 10

    # 8. Verify MVP Phase 403 Gating for Agentic Reasoning Route
    agentic_res = client.post("/api/v1/noah/agentic-reasoning", headers=headers, json={
        "goal": "Autonomous multi-step investigation"
    })
    assert agentic_res.status_code == 403
    assert "reserved for Phase 5 enterprise rollout" in agentic_res.json()["detail"]

    # 9. Verify 401 for unauthenticated protected API calls
    unauth_res = client.get("/api/v1/kpis")
    assert unauth_res.status_code == 401
