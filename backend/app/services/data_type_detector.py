import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import pandas as pd
import numpy as np


class DataTypeDetector:
    """
    Intelligent dynamic schema and column data-type detection engine.
    Inspects actual values and column names to accurately classify data into:
    - Currency
    - Percentage
    - Date
    - Date & Time
    - Integer
    - Decimal
    - Boolean
    - Categorical
    - Identifier
    - Text
    """

    CURRENCY_SYMBOLS = ["$", "€", "£", "₹", "¥", "₩", "د.إ", "AED", "INR", "USD", "EUR", "GBP", "CAD", "AUD"]
    FINANCIAL_KEYWORDS = [
        "price", "revenue", "cost", "salary", "fee", "amount", "mrr", "arr",
        "sales", "spend", "budget", "income", "margin", "aov", "unit_price",
        "total_amount", "ticket_price", "billings", "payable", "receivable",
        "profit", "gross", "net", "subtotal", "val", "valuation"
    ]
    PERCENTAGE_KEYWORDS = [
        "pct", "percent", "percentage", "rate", "ratio", "margin_pct",
        "churn_rate", "discount", "discount_rate", "tax_rate", "conversion_rate",
        "bounce_rate", "growth_rate", "utilization"
    ]
    ID_KEYWORDS = [
        "id", "order_id", "transaction_id", "sku", "code", "part_number",
        "uuid", "hash", "item_code", "product_code", "customer_id", "user_id"
    ]

    @staticmethod
    def safe_float(val: Any, default: float = 0.0) -> float:
        try:
            if val is None or pd.isna(val) or np.isnan(val) or np.isinf(val):
                return default
            return round(float(val), 2)
        except Exception:
            return default

    @classmethod
    def clean_numeric_value(cls, val: Any) -> Optional[float]:
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (int, float, np.integer, np.floating)):
            f = float(val)
            return None if (np.isnan(f) or np.isinf(f)) else f
        s = str(val).strip()
        # Remove currency symbols and common noise
        s = re.sub(r"(?i)\b(rs\.?|inr|usd|eur|gbp|cad|aud|chf|jpy|aed)\b", "", s)
        s = re.sub(r"[$€£₹¥₩%,\s]", "", s)
        # Handle negative parenthesis e.g. (120.50) -> -120.50
        s = re.sub(r"^\((.+)\)$", r"-\1", s)
        try:
            f = float(s)
            return None if (np.isnan(f) or np.isinf(f)) else f
        except Exception:
            return None

    @classmethod
    def detect_column_type(cls, col_name: str, series: pd.Series) -> Dict[str, Any]:
        """
        Inspects a single column's values and name to determine its accurate data type,
        summary statistics, and sample values.
        """
        clean_name = str(col_name).strip()
        col_lower = clean_name.lower().replace(" ", "_")
        non_null_series = series.dropna()
        total_count = len(series)
        non_null_count = len(non_null_series)
        null_count = total_count - non_null_count
        unique_count = int(series.nunique())

        # Prepare representative samples
        sample_raw = non_null_series.head(5).tolist()
        sample_values = [
            str(v) if not isinstance(v, (float, np.floating)) else str(cls.safe_float(v))
            for v in sample_raw
        ]

        if non_null_count == 0:
            return {
                "name": clean_name,
                "data_type": "Text",
                "unit": "text",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": 0,
                "null_count": null_count,
                "unique_count": 0,
                "sample_values": [],
                "stats": {},
            }

        # 1. Check for Boolean
        bool_candidates = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}
        str_vals = non_null_series.astype(str).str.strip().str.lower()
        if unique_count <= 2 and set(str_vals.unique()).issubset(bool_candidates):
            return {
                "name": clean_name,
                "data_type": "Boolean",
                "unit": "boolean",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {"true_count": int(str_vals.isin(["true", "yes", "1", "t", "y"]).sum())},
            }

        # 2. Check for Date / Date & Time
        is_date_col = False
        parsed_dates = None
        
        # Check if already datetime dtype
        if pd.api.types.is_datetime64_any_dtype(series):
            is_date_col = True
            parsed_dates = series.dropna()
        elif not pd.api.types.is_numeric_dtype(series):
            test_samples = non_null_series.head(20).astype(str)
            # Require date patterns or keywords so general text columns aren't parsed as dates
            date_name_match = any(k in col_lower for k in ["date", "time", "timestamp", "dt", "day", "month", "year", "created", "updated", "dob", "period"])
            has_date_pattern = test_samples.str.contains(
                r"^\s*\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}|\d{1,2} (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
                regex=True,
                case=False
            ).any()
            
            if date_name_match or has_date_pattern:
                try:
                    converted = pd.to_datetime(test_samples, errors="coerce", format="mixed")
                    valid_converted = converted.dropna()
                    if len(valid_converted) >= len(test_samples) * 0.7:
                        is_date_col = True
                        parsed_dates = pd.to_datetime(non_null_series, errors="coerce", format="mixed").dropna()
                except Exception:
                    pass

        if is_date_col and parsed_dates is not None and len(parsed_dates) > 0:
            # Check if timestamps have non-zero time components
            has_time_component = any(
                dt.hour != 0 or dt.minute != 0 or dt.second != 0
                for dt in parsed_dates.head(20)
            )
            detected_type = "Date & Time" if has_time_component else "Date"
            min_d_str = None
            max_d_str = None
            try:
                min_d = parsed_dates.min()
                if pd.notna(min_d):
                    min_d_str = min_d.strftime("%Y-%m-%d %H:%M:%S" if has_time_component else "%Y-%m-%d")
            except Exception:
                min_d_str = str(parsed_dates.iloc[0]) if len(parsed_dates) > 0 else None

            try:
                max_d = parsed_dates.max()
                if pd.notna(max_d):
                    max_d_str = max_d.strftime("%Y-%m-%d %H:%M:%S" if has_time_component else "%Y-%m-%d")
            except Exception:
                max_d_str = str(parsed_dates.iloc[-1]) if len(parsed_dates) > 0 else None

            return {
                "name": clean_name,
                "data_type": detected_type,
                "unit": "date",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {
                    "min_date": min_d_str,
                    "max_date": max_d_str,
                },
            }

        # 3. Numeric conversion (fast vectorized path)
        if pd.api.types.is_numeric_dtype(series):
            numeric_cleaned = pd.to_numeric(non_null_series, errors="coerce").dropna()
        else:
            direct_num = pd.to_numeric(non_null_series, errors="coerce").dropna()
            if len(direct_num) >= non_null_count * 0.7:
                numeric_cleaned = direct_num
            else:
                numeric_cleaned = non_null_series.apply(cls.clean_numeric_value).dropna()

        is_numeric = len(numeric_cleaned) >= non_null_count * 0.7 and len(numeric_cleaned) > 0

        # Check for Percentage
        has_percent_symbol = any("%" in str(v) for v in sample_raw)
        has_percent_name = any(kw in col_lower for kw in cls.PERCENTAGE_KEYWORDS)

        if is_numeric and (has_percent_symbol or (has_percent_name and (numeric_cleaned.max() if len(numeric_cleaned) else 0) <= 100.0)):
            return {
                "name": clean_name,
                "data_type": "Percentage",
                "unit": "percentage",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {
                    "min": cls.safe_float(numeric_cleaned.min()),
                    "max": cls.safe_float(numeric_cleaned.max()),
                    "mean": cls.safe_float(numeric_cleaned.mean()),
                },
            }

        # 4. Check for Currency
        has_currency_symbol = any(
            any(sym in str(v) for sym in cls.CURRENCY_SYMBOLS)
            for v in sample_raw
        )
        has_financial_name = any(kw in col_lower for kw in cls.FINANCIAL_KEYWORDS)

        if is_numeric and (has_currency_symbol or has_financial_name):
            return {
                "name": clean_name,
                "data_type": "Currency",
                "unit": "currency",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {
                    "sum": cls.safe_float(numeric_cleaned.sum()),
                    "mean": cls.safe_float(numeric_cleaned.mean()),
                    "min": cls.safe_float(numeric_cleaned.min()),
                    "max": cls.safe_float(numeric_cleaned.max()),
                    "median": cls.safe_float(numeric_cleaned.median()),
                },
            }

        # 5. Check for Identifier / Code
        is_id_name = any(col_lower == kw or col_lower.endswith(f"_{kw}") for kw in cls.ID_KEYWORDS)
        if is_id_name and not any(kw in col_lower for kw in ["units", "quantity", "count", "orders", "visitors", "items"]):
            return {
                "name": clean_name,
                "data_type": "Identifier",
                "unit": "id",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {"cardinality": unique_count},
            }

        # 6. Check for Quantitative Numbers (Integer vs Decimal)
        if is_numeric:
            # Check if all values are exact integers (no fractional decimal component)
            is_all_integers = bool(np.all(np.isclose(numeric_cleaned, np.round(numeric_cleaned))))
            data_type = "Integer" if is_all_integers else "Decimal"
            return {
                "name": clean_name,
                "data_type": data_type,
                "unit": "number",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {
                    "sum": cls.safe_float(numeric_cleaned.sum()),
                    "mean": cls.safe_float(numeric_cleaned.mean()),
                    "min": cls.safe_float(numeric_cleaned.min()),
                    "max": cls.safe_float(numeric_cleaned.max()),
                    "std": cls.safe_float(numeric_cleaned.std()) if len(numeric_cleaned) > 1 else 0.0,
                },
            }

        # 7. Check for Categorical vs Free Text
        if unique_count <= 100 or (unique_count / max(1, non_null_count) < 0.45):
            top_counts = non_null_series.astype(str).value_counts().head(6).to_dict()
            return {
                "name": clean_name,
                "data_type": "Categorical",
                "unit": "categorical",
                "raw_dtype": str(series.dtype),
                "total_count": total_count,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": sample_values,
                "stats": {"top_categories": {str(k): int(v) for k, v in top_counts.items()}},
            }

        # 8. Default: Text
        return {
            "name": clean_name,
            "data_type": "Text",
            "unit": "text",
            "raw_dtype": str(series.dtype),
            "total_count": total_count,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "unique_count": unique_count,
            "sample_values": sample_values,
            "stats": {},
        }

    @classmethod
    def detect_schema(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Inspects the entire DataFrame and returns a comprehensive schema catalog.
        """
        schema: List[Dict[str, Any]] = []
        for col in df.columns:
            if str(col).startswith("_"):
                continue
            col_profile = cls.detect_column_type(col, df[col])
            schema.append(col_profile)
        return schema
