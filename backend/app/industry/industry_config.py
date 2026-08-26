from typing import Dict, List, Any

# Generic & Specialized Industry KPI Presets
RETAIL_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "revenue", "name": "Total Revenue", "description": "Gross sales revenue generated across channels", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "orders", "name": "Total Orders", "description": "Total volume of completed customer orders", "category": "Sales", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "aov", "name": "Average Order Value (AOV)", "description": "Average amount spent per transaction", "category": "Sales", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "conversion_rate", "name": "Conversion Rate", "description": "Percentage of visitors completing purchases", "category": "Marketing", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "units_sold", "name": "Units Sold", "description": "Total physical items sold", "category": "Operations", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

SAAS_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "mrr", "name": "Monthly Recurring Revenue (MRR)", "description": "Predictable monthly subscription revenue", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "arr", "name": "Annual Recurring Revenue (ARR)", "description": "Annualized run-rate subscription revenue", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "churn_rate", "name": "Customer Churn Rate", "description": "Percentage of customers canceling subscriptions", "category": "Retention", "unit": "percentage", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "cac", "name": "Customer Acquisition Cost (CAC)", "description": "Cost to acquire a new paying customer", "category": "Sales & Marketing", "unit": "currency", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "nps", "name": "Net Promoter Score (NPS)", "description": "Customer loyalty and satisfaction index", "category": "Customer Success", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

RESTAURANT_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "daily_sales", "name": "Daily Gross Food Sales", "description": "Total revenue from dining and takeaway orders", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "covers_count", "name": "Total Covers / Guest Count", "description": "Number of guests or meal orders served", "category": "Operations", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "table_turnover", "name": "Table Turnover Rate", "description": "Average seatings per table per shift", "category": "Operations", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "food_cost_pct", "name": "Food Cost Percentage", "description": "Ingredient cost as a percent of food sales", "category": "Financial", "unit": "percentage", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "avg_ticket", "name": "Average Ticket Size", "description": "Average spend per order or customer table", "category": "Sales", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

HEALTHCARE_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "patient_admissions", "name": "Patient Encounters", "description": "Total consultations, admissions, or treatments", "category": "Clinical", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "bed_occupancy_rate", "name": "Bed Occupancy Rate", "description": "Percentage of operational beds currently in use", "category": "Operations", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "avg_treatment_cost", "name": "Average Cost per Encounter", "description": "Operating cost incurred per patient", "category": "Financial", "unit": "currency", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "readmission_rate", "name": "30-Day Readmission Rate", "description": "Percentage of patients readmitted within 30 days", "category": "Quality", "unit": "percentage", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "patient_satisfaction", "name": "Patient Satisfaction Score", "description": "Standardized clinical feedback index", "category": "Quality", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

MANUFACTURING_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "oee", "name": "Overall Equipment Effectiveness (OEE)", "description": "Productivity measure combining availability, performance & quality", "category": "Operations", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "production_output", "name": "Total Production Units", "description": "Finished goods manufactured across lines", "category": "Operations", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "defect_rate", "name": "Scrap / Defect Rate", "description": "Percentage of units failing QA inspection", "category": "Quality", "unit": "percentage", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "downtime_hours", "name": "Unplanned Downtime", "description": "Hours of production stoppage due to maintenance", "category": "Maintenance", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "unit_manufacturing_cost", "name": "Unit Manufacturing Cost", "description": "Direct material and labor cost per finished unit", "category": "Financial", "unit": "currency", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True}
]

FINTECH_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "tpv", "name": "Total Payment Volume (TPV)", "description": "Gross dollar value of processed payment transactions", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "tx_count", "name": "Transaction Count", "description": "Total number of completed financial transfers", "category": "Operations", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "take_rate", "name": "Net Take Rate", "description": "Net revenue earned as percentage of processed volume", "category": "Financial", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "fraud_loss_bps", "name": "Fraud Rate (Basis Points)", "description": "Loss incurred from fraudulent transactions in bps", "category": "Risk & Compliance", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "active_accounts", "name": "Daily Transacting Users", "description": "Unique active accounts executing payments", "category": "Growth", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

HOSPITALITY_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "revpar", "name": "Revenue Per Available Room (RevPAR)", "description": "Total room revenue divided by available rooms", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "occupancy_rate", "name": "Hotel Occupancy Rate", "description": "Percentage of available rooms booked", "category": "Operations", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "adr", "name": "Average Daily Rate (ADR)", "description": "Average rental revenue earned per paid room", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "direct_booking_pct", "name": "Direct Booking Share", "description": "Percentage of bookings completed without OTA commission", "category": "Distribution", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "guest_satisfaction", "name": "Guest Review Score", "description": "Aggregated guest satisfaction index", "category": "Quality", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

EDUCATION_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "active_learners", "name": "Daily Active Learners", "description": "Students or users engaging with learning modules", "category": "Engagement", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "completion_rate", "name": "Course Completion Rate", "description": "Percentage of enrolled learners completing curricula", "category": "Performance", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "student_retention", "name": "Term Retention Rate", "description": "Percentage of students returning for subsequent terms", "category": "Retention", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "avg_assessment_score", "name": "Average Assessment Score", "description": "Mean score across standardized tests", "category": "Academic", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

REAL_ESTATE_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "portfolio_occupancy", "name": "Portfolio Occupancy Rate", "description": "Leased square footage across managed properties", "category": "Operations", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "net_operating_income", "name": "Net Operating Income (NOI)", "description": "Gross revenue minus operating property expenses", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "days_on_market", "name": "Average Days on Market", "description": "Duration before a vacant unit is successfully leased", "category": "Leasing", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "rent_collection_rate", "name": "Rent Collection Efficiency", "description": "Percentage of on-time rental payments collected", "category": "Financial", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True}
]

AUTOMOTIVE_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "units_delivered", "name": "Vehicles Delivered", "description": "Total vehicle sales handed over to customers", "category": "Sales", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "service_revenue", "name": "Aftersales Service Revenue", "description": "Revenue from maintenance, parts & warranty repair", "category": "Financial", "unit": "currency", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "inventory_turn_days", "name": "Vehicle Days in Inventory", "description": "Average lot holding time per vehicle before sale", "category": "Operations", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "warranty_claim_rate", "name": "Warranty Claim Rate", "description": "Service tickets submitted per 1,000 vehicles", "category": "Quality", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True}
]

ENERGY_DEFAULT_KPIS: List[Dict[str, Any]] = [
    {"key": "energy_generated_mwh", "name": "Power Generation (MWh)", "description": "Total electricity delivered to transmission grid", "category": "Generation", "unit": "number", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "grid_efficiency", "name": "Transmission Efficiency", "description": "Ratio of delivered power to generated power", "category": "Operations", "unit": "percentage", "direction": "increase_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "unplanned_outages", "name": "Unplanned Grid Outages", "description": "Total incidents of supply disruption", "category": "Reliability", "unit": "number", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True},
    {"key": "operating_cost_mwh", "name": "Levelized Cost per MWh", "description": "Operating and maintenance cost per megawatt-hour", "category": "Financial", "unit": "currency", "direction": "decrease_is_good", "calculation_cadence": "daily", "is_active": True}
]

INDUSTRY_CONFIGS: Dict[str, Dict[str, Any]] = {
    "Retail/E-commerce": {
        "display_name": "Retail & E-commerce",
        "description": "Multi-channel retail, direct-to-consumer, and online stores",
        "supports_inventory_module": True,
        "default_kpis": RETAIL_DEFAULT_KPIS,
        "primary_dimensions": ["region", "product_category", "sales_channel"],
    },
    "SaaS/Software": {
        "display_name": "SaaS & Cloud Software",
        "description": "Cloud software, recurring billing, and digital subscription services",
        "supports_inventory_module": False,
        "default_kpis": SAAS_DEFAULT_KPIS,
        "primary_dimensions": ["tier", "region", "acquisition_channel"],
    },
    "Restaurants/F&B": {
        "display_name": "Restaurants & Food Services (F&B)",
        "description": "Dining venues, multi-location franchises, and cloud kitchens",
        "supports_inventory_module": True,
        "default_kpis": RESTAURANT_DEFAULT_KPIS,
        "primary_dimensions": ["location", "menu_category", "meal_period"],
    },
    "Healthcare/MedTech": {
        "display_name": "Healthcare & Pharmaceuticals",
        "description": "Hospitals, clinics, medical devices, and health tech providers",
        "supports_inventory_module": True,
        "default_kpis": HEALTHCARE_DEFAULT_KPIS,
        "primary_dimensions": ["department", "facility", "insurance_provider"],
    },
    "Manufacturing/Supply Chain": {
        "display_name": "Manufacturing & Industrial",
        "description": "Assembly lines, discrete manufacturing, and industrial production",
        "supports_inventory_module": True,
        "default_kpis": MANUFACTURING_DEFAULT_KPIS,
        "primary_dimensions": ["facility", "product_line", "shift"],
    },
    "Supply Chain/Logistics": {
        "display_name": "Supply Chain & Logistics",
        "description": "Distribution hubs, freight management, and fulfillment networks",
        "supports_inventory_module": True,
        "default_kpis": RETAIL_DEFAULT_KPIS,
        "primary_dimensions": ["warehouse_location", "carrier", "destination_region"],
    },
    "FinTech/Finance": {
        "display_name": "Banking & FinTech",
        "description": "Payment gateways, digital banking, neo-brokers, and financial services",
        "supports_inventory_module": False,
        "default_kpis": FINTECH_DEFAULT_KPIS,
        "primary_dimensions": ["payment_rail", "user_segment", "country"],
    },
    "Hospitality/Travel": {
        "display_name": "Hospitality & Tourism",
        "description": "Hotels, resorts, airlines, and travel booking platforms",
        "supports_inventory_module": True,
        "default_kpis": HOSPITALITY_DEFAULT_KPIS,
        "primary_dimensions": ["property", "room_type", "booking_source"],
    },
    "Education/EdTech": {
        "display_name": "Education & EdTech",
        "description": "Online academies, universities, and corporate training systems",
        "supports_inventory_module": False,
        "default_kpis": EDUCATION_DEFAULT_KPIS,
        "primary_dimensions": ["program", "cohort", "delivery_mode"],
    },
    "Real Estate/PropTech": {
        "display_name": "Real Estate & Construction",
        "description": "Commercial property, residential leasing, and real estate assets",
        "supports_inventory_module": False,
        "default_kpis": REAL_ESTATE_DEFAULT_KPIS,
        "primary_dimensions": ["property_type", "city", "lease_status"],
    },
    "Automotive/Mobility": {
        "display_name": "Automotive & Mobility",
        "description": "Vehicle dealerships, EV manufacturing, and fleet operations",
        "supports_inventory_module": True,
        "default_kpis": AUTOMOTIVE_DEFAULT_KPIS,
        "primary_dimensions": ["model", "dealership", "region"],
    },
    "Energy & Utilities": {
        "display_name": "Energy, Oil & Utilities",
        "description": "Renewable power generation, oil & gas, and public utility grids",
        "supports_inventory_module": True,
        "default_kpis": ENERGY_DEFAULT_KPIS,
        "primary_dimensions": ["grid_zone", "generation_source", "plant"],
    },
    "Professional Services/Consulting": {
        "display_name": "Professional Services & Consulting",
        "description": "Agencies, legal practices, advisory, and billable service firms",
        "supports_inventory_module": False,
        "default_kpis": SAAS_DEFAULT_KPIS,
        "primary_dimensions": ["practice_area", "client_tier", "engagement_type"],
    },
    "General Enterprise": {
        "display_name": "General Enterprise",
        "description": "Cross-functional enterprise operations and business analytics",
        "supports_inventory_module": True,
        "default_kpis": RETAIL_DEFAULT_KPIS,
        "primary_dimensions": ["business_unit", "region", "channel"],
    },
}


def get_default_kpis_for_industry(industry_name: str) -> List[Dict[str, Any]]:
    # Match exact or partial name
    if industry_name in INDUSTRY_CONFIGS:
        return INDUSTRY_CONFIGS[industry_name]["default_kpis"]
    
    ind_lower = (industry_name or "").lower()

    if "saas" in ind_lower or "subscription" in ind_lower or "software" in ind_lower or "cloud" in ind_lower:
        return SAAS_DEFAULT_KPIS
    if "restaurant" in ind_lower or "food" in ind_lower or "f&b" in ind_lower or "dining" in ind_lower:
        return RESTAURANT_DEFAULT_KPIS
    if "health" in ind_lower or "clinic" in ind_lower or "hospital" in ind_lower or "pharma" in ind_lower:
        return HEALTHCARE_DEFAULT_KPIS
    if "manufacturing" in ind_lower or "industrial" in ind_lower or "factory" in ind_lower:
        return MANUFACTURING_DEFAULT_KPIS
    if "fintech" in ind_lower or "bank" in ind_lower or "finance" in ind_lower:
        return FINTECH_DEFAULT_KPIS
    if "hotel" in ind_lower or "hospitality" in ind_lower or "travel" in ind_lower:
        return HOSPITALITY_DEFAULT_KPIS
    if "education" in ind_lower or "edtech" in ind_lower or "school" in ind_lower:
        return EDUCATION_DEFAULT_KPIS
    if "real estate" in ind_lower or "property" in ind_lower or "proptech" in ind_lower:
        return REAL_ESTATE_DEFAULT_KPIS
    if "auto" in ind_lower or "vehicle" in ind_lower or "mobility" in ind_lower:
        return AUTOMOTIVE_DEFAULT_KPIS
    if "energy" in ind_lower or "utility" in ind_lower or "power" in ind_lower:
        return ENERGY_DEFAULT_KPIS
    
    for key, cfg in INDUSTRY_CONFIGS.items():
        if key.lower() in ind_lower or cfg["display_name"].lower() in ind_lower:
            return cfg["default_kpis"]
            
    return RETAIL_DEFAULT_KPIS
