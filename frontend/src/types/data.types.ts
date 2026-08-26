export interface ValidationErrorItem {
  row: number;
  column: string;
  value: any;
  error_message: string;
}

export interface DataValidationResult {
  is_valid: boolean;
  total_rows: number;
  valid_rows: number;
  error_count: number;
  errors: ValidationErrorItem[];
  columns_detected: string[];
  sample_preview: Record<string, any>[];
}

export interface IngestionResponse {
  file_name: string;
  status: 'success' | 'partial_success' | 'failed';
  total_rows: number;
  processed_rows: number;
  validation_summary: DataValidationResult;
  kpis_updated: string[];
  message: string;
}
