export interface RootCauseResult {
  id: number;
  company_id: number;
  detection_id: number;
  dimension_name: string;
  dimension_value: string;
  contribution_percentage: number;
  explanation_text: string;
  confidence_score: number;
  created_at: string;
}

export interface DetectionEvent {
  id: number;
  company_id: number;
  kpi_id: number;
  kpi_name?: string;
  detected_at: string;
  direction: 'up' | 'down' | 'anomaly';
  magnitude: number;
  percentage_change: number;
  baseline_value: number;
  current_value: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  root_causes: RootCauseResult[];
}
