from typing import List, Dict, Any

SAAS_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {
        "key": "mrr",
        "name": "Monthly Recurring Revenue (MRR)",
        "description": "Total predictable recurring revenue normalized to a monthly value",
        "category": "Financial",
        "unit": "currency",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "churn_rate",
        "name": "Customer Churn Rate",
        "description": "Percentage of customers canceling subscriptions during the period",
        "category": "Customer Success",
        "unit": "percentage",
        "direction": "decrease_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "activation_rate",
        "name": "User Activation Rate",
        "description": "Percentage of signed-up users who reach their activation milestone",
        "category": "Product",
        "unit": "percentage",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "arpu",
        "name": "Average Revenue Per User (ARPU)",
        "description": "Average revenue generated per active subscription account",
        "category": "Financial",
        "unit": "currency",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "active_users",
        "name": "Daily Active Users (DAU)",
        "description": "Unique active accounts engaging with the platform daily",
        "category": "Product",
        "unit": "count",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    }
]
