import sys
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.services.dataset_store import TenantDatasetStore
from app.ml.root_cause.contribution_analyzer import ContributionAnalyzer

client = TestClient(app)

def test_root_cause_contributions():
    print("Testing Root Cause Contribution Analyzer with Multi-Dimensional Variance Data...")

    # 1. Test ContributionAnalyzer directly with distinct multi-dimensional variations
    dim_data_current = {
        "outlet_name": {"T. Nagar": 4500.0, "Velachery": 8000.0, "Anna Nagar": 7500.0},
        "food_category": {"Biryani": 6000.0, "Starters": 9000.0, "Desserts": 5000.0},
        "channel": {"Dine-In": 7000.0, "Takeaway": 5000.0, "Online": 8000.0},
        "_row_label": "2026-08-25",
        "order_id": "ORD-999"
    }

    dim_data_baseline = {
        "outlet_name": {"T. Nagar": 9000.0, "Velachery": 8200.0, "Anna Nagar": 7600.0},  # T Nagar dropped 4500
        "food_category": {"Biryani": 8000.0, "Starters": 9500.0, "Desserts": 5100.0},    # Biryani dropped 2000
        "channel": {"Dine-In": 7800.0, "Takeaway": 5200.0, "Online": 8800.0},          # Online dropped 800
        "_row_label": "2026-08-18",
        "order_id": "ORD-111"
    }

    results = ContributionAnalyzer.analyze_dimension_contributions(
        current_dim_data=dim_data_current,
        baseline_dim_data=dim_data_baseline,
        overall_change=7300.0,
        direction="down",
        kpi_name="Revenue"
    )

    print(f"Computed {len(results)} root cause dimensions:")
    for r in results:
        print(f"  - Dimension: {r['dimension_name']} -> Slice: {r['dimension_value']} | Contribution: {r['contribution_percentage']}% | Exp: {r['explanation_text']}")

    assert len(results) >= 2, "Expected multiple contributing dimensions"
    
    # Check that technical metadata / order_id / _row_label were excluded
    dim_names = [r["dimension_name"] for r in results]
    assert "_row_label" not in dim_names
    assert "order_id" not in dim_names

    # Check that percentages are distinct and reflect the relative variance
    percentages = [r["contribution_percentage"] for r in results]
    assert len(set(percentages)) == len(percentages), f"Percentages must all be distinct, got {percentages}"
    assert percentages[0] > percentages[1] > percentages[2], f"Expected descending order of contribution, got {percentages}"
    print("[PASS] Contribution Analyzer calculated distinct, mathematically normalized weights!")

    # 2. Test End-to-End Test Anomaly Trigger via API
    # Register/Login
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

    # Trigger test anomaly
    ano_res = client.post("/api/v1/detections/test-anomaly", headers=headers)
    assert ano_res.status_code == 200, f"Failed to create test anomaly: {ano_res.text}"
    anomaly = ano_res.json()
    assert "id" in anomaly
    det_id = anomaly["id"]

    # Fetch detections
    det_list_res = client.get("/api/v1/detections", headers=headers)
    assert det_list_res.status_code == 200
    detections = det_list_res.json()
    matching = [d for d in detections if d["id"] == det_id]
    assert len(matching) > 0
    det_obj = matching[0]

    root_causes = det_obj.get("root_causes", [])
    print(f"API Returned {len(root_causes)} Root Causes for Test Anomaly #{det_id}:")
    for rc in root_causes:
        print(f"  - {rc['dimension_name']}: {rc['dimension_value']} ({rc['contribution_percentage']}%) => {rc['explanation_text']}")

    rc_percentages = [rc["contribution_percentage"] for rc in root_causes]
    assert len(set(rc_percentages)) == len(rc_percentages), f"API Root Causes must have distinct weights, got {rc_percentages}"
    print("[PASS] End-to-End API returned distinct, non-identical root cause contributions!")

if __name__ == "__main__":
    test_root_cause_contributions()
    print("\n=======================================================")
    print("ROOT CAUSE CONTRIBUTION ENGINE: 100% PASS AND VERIFIED!")
    print("=======================================================")
