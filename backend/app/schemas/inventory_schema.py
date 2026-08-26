from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class InventoryItemOut(BaseModel):
    id: int
    company_id: int
    warehouse_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    warehouse_region: Optional[str] = None
    sku: str
    name: str
    category: Optional[str] = None
    current_stock: float
    reorder_point: float
    cost_price: float
    selling_price: float
    stockout_risk: str = "low"  # "low", "medium", "critical"
    projected_days_left: int = 30
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseLocationOut(BaseModel):
    id: int
    company_id: int
    name: str
    code: str
    region: str
    capacity: float
    current_utilization: float = 0.0
    item_count: int = 0
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryAllocationRecommendation(BaseModel):
    id: str
    sku: str
    product_name: str
    source_warehouse_id: int
    source_warehouse_name: str
    source_region: str
    dest_warehouse_id: int
    dest_warehouse_name: str
    dest_region: str
    units_to_transfer: int
    reason: str
    expected_impact: str
    urgency: str = "high"  # "high", "medium", "low"
    item_id: Optional[int] = None


class InventoryDashboardSummary(BaseModel):
    status: str
    total_items: int
    total_warehouses: int
    critical_stock_count: int
    total_inventory_value: float
    average_capacity_utilization: float
    warehouses: List[WarehouseLocationOut] = []
    items: List[InventoryItemOut] = []
    allocations: List[InventoryAllocationRecommendation] = []
    message: str
