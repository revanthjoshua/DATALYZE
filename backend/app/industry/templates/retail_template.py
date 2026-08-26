from typing import List, Dict, Any

RETAIL_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {
        "key": "revenue",
        "name": "Total Revenue",
        "description": "Gross sales revenue generated across all sales channels",
        "category": "Financial",
        "unit": "currency",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "orders",
        "name": "Total Orders",
        "description": "Total volume of completed customer orders",
        "category": "Sales",
        "unit": "count",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "aov",
        "name": "Average Order Value (AOV)",
        "description": "Average amount spent by customers per transaction",
        "category": "Sales",
        "unit": "currency",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "conversion_rate",
        "name": "Conversion Rate",
        "description": "Percentage of store visitors who completed a purchase",
        "category": "Marketing",
        "unit": "percentage",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    },
    {
        "key": "units_sold",
        "name": "Units Sold",
        "description": "Total physical items sold across all product categories",
        "category": "Operational",
        "unit": "count",
        "direction": "increase_is_good",
        "calculation_cadence": "daily",
        "is_active": True,
    }
]
