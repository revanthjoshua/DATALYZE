export interface KPIDefinition {
  id: number;
  company_id: number;
  key: string;
  name: string;
  description?: string;
  category: string;
  unit: string;
  direction: 'increase_is_good' | 'decrease_is_good' | string;
  calculation_cadence: string;
  is_active: boolean;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

export interface KPIValue {
  id: number;
  company_id: number;
  kpi_id: number;
  timestamp: string;
  value: number;
  dimension_data?: Record<string, Record<string, number>>;
  source_file?: string;
  created_at: string;
}

export interface KPISummaryCard {
  id: number;
  key: string;
  name: string;
  description?: string;
  category: string;
  unit: string;
  direction: string;
  calculation_cadence?: string;
  current_value?: number;
  previous_value?: number;
  percentage_change?: number;
  trend_direction?: 'up' | 'down' | 'neutral';
  status: 'healthy' | 'warning' | 'critical';
  recent_history: KPIValue[];
}
