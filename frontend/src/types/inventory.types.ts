export interface InventoryItem {
  id: number;
  company_id: number;
  warehouse_id?: number;
  warehouse_name?: string;
  warehouse_region?: string;
  sku: string;
  name: string;
  category?: string;
  current_stock: number;
  reorder_point: number;
  cost_price: number;
  selling_price: number;
  stockout_risk: 'low' | 'medium' | 'critical';
  projected_days_left: number;
  created_at: string;
}

export interface WarehouseLocation {
  id: number;
  company_id: number;
  name: string;
  code: string;
  region: string;
  capacity: number;
  current_utilization: number;
  item_count: number;
  is_active: boolean;
  created_at: string;
}

export interface InventoryAllocationRecommendation {
  id: string;
  sku: string;
  product_name: string;
  source_warehouse_id: number;
  source_warehouse_name: string;
  source_region: string;
  dest_warehouse_id: number;
  dest_warehouse_name: string;
  dest_region: string;
  units_to_transfer: number;
  reason: string;
  expected_impact: string;
  urgency: 'high' | 'medium' | 'low';
  item_id?: number;
}

export interface InventoryDashboardSummary {
  status: string;
  total_items: number;
  total_warehouses: number;
  critical_stock_count: number;
  total_inventory_value: number;
  average_capacity_utilization: number;
  warehouses: WarehouseLocation[];
  items: InventoryItem[];
  allocations: InventoryAllocationRecommendation[];
  message: string;
}
