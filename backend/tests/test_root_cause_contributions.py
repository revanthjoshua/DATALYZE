import pandas as pd
import pytest
from app.ml.root_cause.contribution_analyzer import ContributionAnalyzer


def test_contribution_analyzer_distinct_percentages_on_dataframe():
    """Verify that multiple contributing dimensions and slices receive distinct percentages."""
    data = {
        "Outlet": ["Store A"] * 10 + ["Store B"] * 10 + ["Store C"] * 10 + ["Store D"] * 10,
        "Region": ["North"] * 20 + ["South"] * 20,
        "Category": ["Electronics"] * 20 + ["Apparel"] * 20,
        "Revenue": [100.0] * 30 + [20.0] * 10  # recent drop in Store D / South / Apparel
    }
    df = pd.DataFrame(data)

    results = ContributionAnalyzer.analyze_from_dataset(
        df=df,
        kpi_col="Revenue",
        dimension_cols=["Outlet", "Region", "Category"],
        direction="down",
        overall_change=80.0,
        kpi_name="Revenue"
    )

    assert len(results) >= 2, "Should return at least 2 contributing factors"
    pcts = [r["contribution_percentage"] for r in results]
    assert len(pcts) == len(set(pcts)), f"Percentages must be strictly distinct and unique: {pcts}"
    assert all(p > 0 for p in pcts), "Contribution percentages must be positive variance shares"


def test_contribution_analyzer_distinct_percentages_on_dimension_slices():
    """Verify dimension slices analysis produces distinct percentages without duplicates."""
    current_dims = {
        "channel": {"Direct Delivery": 120.0, "Retail Walk-In": 450.0},
        "outlet": {"Store North": 90.0, "Store South": 310.0}
    }
    baseline_dims = {
        "channel": {"Direct Delivery": 300.0, "Retail Walk-In": 500.0},
        "outlet": {"Store North": 250.0, "Store South": 320.0}
    }

    results = ContributionAnalyzer.analyze_dimension_contributions(
        current_dim_data=current_dims,
        baseline_dim_data=baseline_dims,
        overall_change=240.0,
        direction="down",
        kpi_name="Sales"
    )

    assert len(results) >= 2, "Should identify at least 2 contributing dimensions"
    pcts = [r["contribution_percentage"] for r in results]
    assert len(pcts) == len(set(pcts)), f"Percentages must be distinct: {pcts}"
