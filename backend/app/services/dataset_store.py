from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.services.data_type_detector import DataTypeDetector


class TenantDatasetStore:
    """
    In-memory and cached tabular dataset repository per tenant workspace.
    Holds the full raw DataFrame, column catalog, dynamic schema descriptors,
    and fast statistical query primitives for Noah AI and analytics engines.
    """
    _store: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def set_dataset(
        cls,
        tenant_id: int,
        df: pd.DataFrame,
        source_filename: str = "dataset.csv",
        detected_profile: Optional[Dict[str, Any]] = None
    ) -> None:
        clean_df = df.copy()

        # Run dynamic data type detection across all columns
        schema_list = DataTypeDetector.detect_schema(clean_df)
        columns_profile: Dict[str, Any] = {col_info["name"]: col_info for col_info in schema_list}

        # Categorize columns based on detected dynamic types
        numeric_cols = [
            c["name"] for c in schema_list
            if c["data_type"] in ["Currency", "Percentage", "Integer", "Decimal"]
        ]
        categorical_cols = [
            c["name"] for c in schema_list
            if c["data_type"] in ["Categorical", "Boolean", "Text"]
        ]
        datetime_cols = [
            c["name"] for c in schema_list
            if c["data_type"] in ["Date", "Date & Time"]
        ]

        # Completely replace the tenant store with fresh dataset state
        cls._store[tenant_id] = {
            "df": clean_df,
            "filename": source_filename,
            "ingested_at": datetime.now(timezone.utc),
            "row_count": len(clean_df),
            "col_count": len([c for c in clean_df.columns if not str(c).startswith("_")]),
            "columns": [c for c in clean_df.columns if not str(c).startswith("_")],
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "schema": schema_list,
            "columns_profile": columns_profile,
            "dtypes": {col: str(dtype) for col, dtype in clean_df.dtypes.items()},
            "detected_profile": detected_profile or {},
        }

    @classmethod
    def clear_dataset(cls, tenant_id: int) -> bool:
        """Purges in-memory dataset cache for specific tenant workspace."""
        if tenant_id in cls._store:
            del cls._store[tenant_id]
            return True
        return False

    @classmethod
    def clear_all(cls) -> None:
        """Clears all in-memory datasets (used for test resets)."""
        cls._store.clear()

    @classmethod
    def get_dataset(cls, tenant_id: int) -> Optional[pd.DataFrame]:
        tenant_data = cls._store.get(tenant_id)
        if tenant_data and "df" in tenant_data:
            return tenant_data["df"]
        return None


    @classmethod
    def get_metadata(cls, tenant_id: int) -> Optional[Dict[str, Any]]:
        tenant_data = cls._store.get(tenant_id)
        if not tenant_data:
            return None
        return {
            "filename": tenant_data.get("filename"),
            "ingested_at": tenant_data.get("ingested_at").isoformat() if tenant_data.get("ingested_at") else None,
            "row_count": tenant_data.get("row_count", 0),
            "col_count": tenant_data.get("col_count", 0),
            "columns": tenant_data.get("columns", []),
            "numeric_columns": tenant_data.get("numeric_columns", []),
            "categorical_columns": tenant_data.get("categorical_columns", []),
            "datetime_columns": tenant_data.get("datetime_columns", []),
            "schema": tenant_data.get("schema", []),
            "columns_profile": tenant_data.get("columns_profile", {}),
            "dtypes": tenant_data.get("dtypes", {}),
            "detected_profile": tenant_data.get("detected_profile", {}),
        }

    @classmethod
    def get_detected_profile(cls, tenant_id: int) -> Optional[Dict[str, Any]]:
        tenant_data = cls._store.get(tenant_id)
        if not tenant_data:
            return None
        return tenant_data.get("detected_profile")

    @classmethod
    def get_preview(cls, tenant_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        df = cls.get_dataset(tenant_id)
        if df is None or df.empty:
            return {"total_rows": 0, "columns": [], "records": []}

        sliced_df = df.iloc[offset : offset + limit].copy()
        public_cols = [c for c in sliced_df.columns if not str(c).startswith("_")]
        sliced_df = sliced_df[public_cols]

        records = sliced_df.to_dict(orient="records")
        for rec in records:
            for k, v in list(rec.items()):
                if isinstance(v, (datetime, pd.Timestamp)):
                    rec[k] = v.strftime("%Y-%m-%d %H:%M:%S")
                elif pd.isna(v) or v is None:
                    rec[k] = None
                elif isinstance(v, (np.floating, float)):
                    rec[k] = round(float(v), 4)
                elif isinstance(v, (np.integer, int)):
                    rec[k] = int(v)

        meta = cls.get_metadata(tenant_id) or {}

        return {
            "total_rows": len(df),
            "offset": offset,
            "limit": limit,
            "columns": public_cols,
            "schema": meta.get("schema", []),
            "records": records
        }

    @classmethod
    def get_column_values(cls, tenant_id: int, col_name: str, limit: int = 50) -> Dict[str, Any]:
        df = cls.get_dataset(tenant_id)
        if df is None or col_name not in df.columns:
            return {"column": col_name, "unique_count": 0, "values": []}

        series = df[col_name].dropna()
        counts = series.value_counts().head(limit).to_dict()
        return {
            "column": col_name,
            "unique_count": int(series.nunique()),
            "total_non_null": int(len(series)),
            "values": [{"value": str(k), "count": int(v)} for k, v in counts.items()]
        }

    @classmethod
    def execute_query(
        cls,
        tenant_id: int,
        filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None,
        agg_col: Optional[str] = None,
        agg_func: str = "sum",
        sort_by: Optional[str] = None,
        ascending: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        df = cls.get_dataset(tenant_id)
        if df is None or df.empty:
            return {"success": False, "results": [], "count": 0}

        query_df = df.copy()

        # 1. Apply row filters
        if filters:
            for col, val in filters.items():
                if col in query_df.columns and val is not None:
                    query_df = query_df[query_df[col].astype(str) == str(val)]

        # 2. Group By Aggregation
        if group_by and group_by in query_df.columns:
            if agg_col and agg_col in query_df.columns:
                target_series = pd.to_numeric(query_df[agg_col], errors="coerce")
                grouped = query_df.assign(**{agg_col: target_series}).groupby(group_by)[agg_col]

                if agg_func == "mean":
                    res = grouped.mean()
                elif agg_func == "min":
                    res = grouped.min()
                elif agg_func == "max":
                    res = grouped.max()
                elif agg_func == "count":
                    res = grouped.count()
                else:
                    res = grouped.sum()

                sorted_res = res.sort_values(ascending=ascending).head(limit)
                results_list = [
                    {
                        group_by: str(k),
                        f"{agg_func}_{agg_col}": round(float(v), 2) if isinstance(v, (float, np.floating)) else int(v),
                        "value": round(float(v), 2) if isinstance(v, (float, np.floating)) else int(v)
                    }
                    for k, v in sorted_res.items()
                ]
                return {
                    "success": True,
                    "group_by": group_by,
                    "agg_col": agg_col,
                    "agg_func": agg_func,
                    "count": len(results_list),
                    "results": results_list
                }
            else:
                counts = query_df.groupby(group_by).size().sort_values(ascending=ascending).head(limit)
                results_list = [
                    {
                        group_by: str(k),
                        "count": int(v),
                        "value": int(v)
                    }
                    for k, v in counts.items()
                ]
                return {
                    "success": True,
                    "group_by": group_by,
                    "agg_func": "count",
                    "count": len(results_list),
                    "results": results_list
                }

        # 3. Simple column aggregation without group by
        if agg_col and agg_col in query_df.columns:
            target_series = pd.to_numeric(query_df[agg_col], errors="coerce").dropna()
            if agg_func == "mean":
                val = round(float(target_series.mean()), 2)
            elif agg_func == "min":
                val = round(float(target_series.min()), 2)
            elif agg_func == "max":
                val = round(float(target_series.max()), 2)
            elif agg_func == "count":
                val = int(len(target_series))
            else:
                val = round(float(target_series.sum()), 2)
            return {
                "success": True,
                "agg_col": agg_col,
                "agg_func": agg_func,
                "result": val,
                "value": val
            }

        return {"success": False, "results": [], "count": 0}

    @classmethod
    def analyze_query(cls, tenant_id: int, query_text: str) -> Dict[str, Any]:
        """
        Extracts semantic insights and computes statistics from the active dataset for Noah AI.
        """
        df = cls.get_dataset(tenant_id)
        if df is None or df.empty:
            return {"has_data": False, "matched_metrics": [], "matched_categories": {}, "matched_values": []}

        meta = cls.get_metadata(tenant_id) or {}
        q_lower = query_text.lower()

        matched_metrics = []
        numeric_cols = meta.get("numeric_columns", [])
        for num_col in numeric_cols:
            col_words = num_col.replace("_", " ").lower().split()
            # If the full column name or key terms appear in query
            if num_col.lower() in q_lower or any(w in q_lower for w in col_words if len(w) > 2) or (num_col.lower() in ["revenue", "sales", "energy_kwh", "units", "amount", "mrr", "orders"]):
                series = pd.to_numeric(df[num_col], errors="coerce").dropna()
                if len(series) > 0:
                    matched_metrics.append({
                        "name": num_col,
                        "display_name": num_col.replace("_", " ").title(),
                        "total": round(float(series.sum()), 2),
                        "average": round(float(series.mean()), 2),
                        "min": round(float(series.min()), 2),
                        "max": round(float(series.max()), 2),
                        "count": int(len(series)),
                    })

        # If no specific metric was mentioned, include top 2 numeric metrics by default
        if not matched_metrics and numeric_cols:
            for num_col in numeric_cols[:2]:
                series = pd.to_numeric(df[num_col], errors="coerce").dropna()
                if len(series) > 0:
                    matched_metrics.append({
                        "name": num_col,
                        "display_name": num_col.replace("_", " ").title(),
                        "total": round(float(series.sum()), 2),
                        "average": round(float(series.mean()), 2),
                        "min": round(float(series.min()), 2),
                        "max": round(float(series.max()), 2),
                        "count": int(len(series)),
                    })

        matched_categories: Dict[str, Any] = {}
        categorical_cols = meta.get("categorical_columns", [])
        target_num_col = numeric_cols[0] if numeric_cols else None

        for cat_col in categorical_cols:
            if cat_col.lower() in q_lower or any(w in q_lower for w in cat_col.replace("_", " ").split() if len(w) > 2) or len(categorical_cols) <= 2:
                if target_num_col and target_num_col in df.columns:
                    breakdown = df.assign(
                        _num=pd.to_numeric(df[target_num_col], errors="coerce")
                    ).groupby(cat_col)["_num"].sum().dropna().to_dict()
                    matched_categories[cat_col] = {
                        "metric": target_num_col.replace("_", " ").title(),
                        "breakdown": {str(k): round(float(v), 2) for k, v in breakdown.items()}
                    }
                else:
                    breakdown = df.groupby(cat_col).size().to_dict()
                    matched_categories[cat_col] = {
                        "metric": "records",
                        "breakdown": {str(k): int(v) for k, v in breakdown.items()}
                    }

        return {
            "has_data": True,
            "matched_metrics": matched_metrics,
            "matched_categories": matched_categories,
            "matched_values": [],
            "row_count": len(df),
            "filename": meta.get("filename", "dataset.csv")
        }
