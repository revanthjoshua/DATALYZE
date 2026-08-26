from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ValidationErrorItem(BaseModel):
    row: int
    column: str
    value: Any
    error_message: str


class DataValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    error_count: int
    errors: List[ValidationErrorItem] = []
    columns_detected: List[str] = []
    sample_preview: List[Dict[str, Any]] = []
    detected_schema: List[Dict[str, Any]] = []


class IngestionResponse(BaseModel):
    file_name: str
    status: str  # "success", "partial_success", "failed"
    total_rows: int
    processed_rows: int
    validation_summary: DataValidationResult
    kpis_updated: List[str] = []
    detected_schema: List[Dict[str, Any]] = []
    message: str
