export interface Prediction {
  id: number;
  company_id: number;
  kpi_id: number;
  kpi_name?: string;
  forecast_date: string;
  predicted_value: number;
  range_low: number;
  range_high: number;
  confidence_level: 'low' | 'moderate' | 'high';
  method: string;
  model_details?: Record<string, any>;
  created_at: string;
}

export interface Recommendation {
  id: number;
  company_id: number;
  kpi_id?: number;
  kpi_name?: string;
  detection_id?: number;
  prediction_id?: number;
  title: string;
  action_text: string;
  rationale?: string;
  impact_level: 'low' | 'medium' | 'high';
  priority: 'urgent' | 'standard' | 'low';
  category: string;
  status: 'open' | 'in_progress' | 'completed' | 'dismissed';
  created_at: string;
}

export interface Alert {
  id: number;
  company_id: number;
  kpi_id?: number;
  detection_id?: number;
  recommendation_id?: number;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  is_read: boolean;
  created_at: string;
}

export interface NoahDataReference {
  source_type: string;
  title: string;
  value?: string;
  details?: Record<string, any>;
}

export interface NoahQueryResponse {
  question: string;
  answer: string;
  structured_data?: Record<string, any>;
  references: NoahDataReference[];
  suggested_actions: string[];
  timestamp: string;
}

export interface NoahAgenticStep {
  step_index: number;
  title: string;
  stage: 'understand' | 'inspect' | 'slice' | 'forecast' | 'prescribe';
  tool_called: string;
  status: 'completed' | 'in_progress';
  duration_ms: number;
  summary: string;
  details?: Record<string, any>;
}

export interface NoahAgenticPlanResponse {
  goal: string;
  company_name: string;
  execution_time_ms: number;
  steps: NoahAgenticStep[];
  executive_insight: string;
  synthesized_recommendation: string;
  confidence_score: number;
  timestamp: string;
}
