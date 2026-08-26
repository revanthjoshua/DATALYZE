from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import numpy as np


class Forecaster:
    """
    Mathematical Ordinary Least Squares (OLS) Predictive Forecaster
    with dynamic time intervals, expanding prediction bounds,
    and 7-day cyclical seasonality decomposition.
    """

    @classmethod
    def forecast_kpi(
        cls,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Calculates forward predictions from historical values with strict statistical bounds.
        Supports:
        - forecast_kpi(history_list, horizon_days=7, is_non_negative=True)
        - forecast_kpi(values_list, timestamps_list, horizon_days=7, is_non_negative=True)
        """
        history: List[Dict[str, Any]] = []
        horizon_days = kwargs.get("horizon_days", 7)
        is_non_negative = kwargs.get("is_non_negative", True)

        if len(args) >= 2 and isinstance(args[0], (list, tuple)) and isinstance(args[1], (list, tuple)):
            vals, times = args[0], args[1]
            history = [{"value": v, "timestamp": t} for v, t in zip(vals, times)]
        elif len(args) >= 1 and isinstance(args[0], (list, tuple)):
            first_item = args[0][0] if len(args[0]) > 0 else None
            if isinstance(first_item, dict):
                history = list(args[0])
            elif isinstance(first_item, (int, float, np.number)):
                history = [{"value": v, "timestamp": datetime.now(timezone.utc)} for v in args[0]]
            else:
                history = list(args[0])
        elif "history" in kwargs:
            history = kwargs["history"]

        # 1. Filter and sort valid historical data points
        valid_points = [
            p for p in history
            if p.get("value") is not None and not np.isnan(float(p["value"]))
        ]

        if not valid_points:
            return []

        # Sort chronologically
        sorted_points = sorted(valid_points, key=lambda x: x["timestamp"])
        sorted_values = [float(p["value"]) for p in sorted_points]
        sorted_timestamps = [p["timestamp"] for p in sorted_points]

        n = len(sorted_values)

        # Single historical observation fallback
        if n == 1:
            val = sorted_values[0]
            last_ts = sorted_timestamps[0] if sorted_timestamps else datetime.now(timezone.utc)
            base_uncertainty = max(abs(val) * 0.1, 1.0)
            preds = []
            for step in range(1, horizon_days + 1):
                f_date = last_ts + timedelta(days=step)
                p_val = round(val, 2)
                preds.append({
                    "forecast_date": f_date,
                    "predicted_value": p_val,
                    "range_low": max(0.0, round(val - base_uncertainty * (1.0 + step * 0.05), 2)) if is_non_negative else round(val - base_uncertainty * (1.0 + step * 0.05), 2),
                    "range_high": round(val + base_uncertainty * (1.0 + step * 0.05), 2),
                    "confidence_level": "low",
                    "method": "Constant Baseline (Single Observation)",
                    "model_details": {
                        "historical_samples": 1,
                        "residual_std": round(base_uncertainty, 2),
                        "r_squared": 0.0,
                    }
                })
            return preds

        # 2. Ordinary Least Squares (OLS) Linear Regression Fit
        x = np.arange(n, dtype=float)
        y = np.array(sorted_values, dtype=float)

        x_mean = np.mean(x)
        y_mean = np.mean(y)

        ss_x = np.sum((x - x_mean) ** 2)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))

        if ss_x > 1e-9:
            slope = ss_xy / ss_x
            intercept = y_mean - slope * x_mean
        else:
            slope = 0.0
            intercept = y_mean

        y_fitted = slope * x + intercept
        residuals = y - y_fitted

        # Standard Error of Regression (Degrees of freedom = n - 2)
        df_residuals = max(1, n - 2)
        residual_std = float(np.sqrt(np.sum(residuals ** 2) / df_residuals))

        # Coefficient of Determination (R²)
        ss_tot = np.sum((y - y_mean) ** 2)
        if ss_tot > 1e-9:
            ss_res = np.sum(residuals ** 2)
            r_squared = max(0.0, min(1.0, 1.0 - (ss_res / ss_tot)))
        else:
            r_squared = 1.0

        # Confidence Level & z-score multiplier based on sample size and fit
        if n >= 14 and r_squared > 0.4:
            confidence_level = "high"
            z_factor = 1.96  # 95% confidence
        elif n >= 5:
            confidence_level = "moderate"
            z_factor = 1.96
        else:
            confidence_level = "moderate" if n >= 3 else "low"
            z_factor = 2.15

        # 3. Extract Day-of-Week Seasonality (if >= 14 observations)
        seasonal_factors = np.zeros(7)
        has_seasonality = False
        if n >= 14 and sorted_timestamps:
            dow_residuals = [[] for _ in range(7)]
            for i, ts in enumerate(sorted_timestamps):
                if hasattr(ts, "weekday"):
                    dow = ts.weekday()
                    dow_residuals[dow].append(residuals[i])

            for dow in range(7):
                if dow_residuals[dow]:
                    seasonal_factors[dow] = float(np.mean(dow_residuals[dow]))
            has_seasonality = True

        # 4. Resolve Timestamp Step Frequency
        if sorted_timestamps and len(sorted_timestamps) >= 2:
            deltas = [
                (sorted_timestamps[i] - sorted_timestamps[i - 1]).total_seconds()
                for i in range(1, len(sorted_timestamps))
            ]
            median_delta_sec = float(np.median(deltas))
            if median_delta_sec <= 0:
                median_delta_sec = 86400.0
            step_delta = timedelta(seconds=median_delta_sec)
        else:
            step_delta = timedelta(days=1)

        last_timestamp = sorted_timestamps[-1] if sorted_timestamps else datetime.now(timezone.utc)
        predictions: List[Dict[str, Any]] = []

        # 5. Generate Forward Predictions
        for step in range(1, horizon_days + 1):
            future_date = last_timestamp + (step_delta * step)
            future_x = (n - 1) + step

            # Base linear trend prediction
            base_pred = slope * future_x + intercept

            # Add seasonal component if available
            if has_seasonality and hasattr(future_date, "weekday"):
                season_adj = seasonal_factors[future_date.weekday()]
            else:
                season_adj = 0.0

            raw_pred = base_pred + season_adj
            final_pred = max(0.0, raw_pred) if is_non_negative else raw_pred

            # Exact expanding prediction interval formula for OLS regression
            if n > 2 and ss_x > 1e-9:
                leverage = 1.0 + (1.0 / n) + (((future_x - x_mean) ** 2) / ss_x)
                horizon_spread = z_factor * residual_std * np.sqrt(leverage)
            else:
                horizon_spread = z_factor * residual_std * np.sqrt(1.0 + (step / max(1, n)))

            p_val = round(float(final_pred), 2)
            if is_non_negative:
                r_low = max(0.0, min(p_val, round(final_pred - horizon_spread, 2)))
                r_high = max(p_val, round(final_pred + horizon_spread, 2))
            else:
                r_low = min(p_val, round(final_pred - horizon_spread, 2))
                r_high = max(p_val, round(final_pred + horizon_spread, 2))

            method_name = "Linear Trend + 7-Day Cyclic Seasonality" if has_seasonality else "Linear Trend Regression"

            predictions.append({
                "forecast_date": future_date,
                "predicted_value": p_val,
                "range_low": r_low,
                "range_high": r_high,
                "confidence_level": confidence_level,
                "method": method_name,
                "model_details": {
                    "historical_samples": n,
                    "trend_slope": round(float(slope), 4),
                    "residual_std": round(residual_std, 2),
                    "r_squared": round(float(r_squared), 3),
                    "seasonality_quality": "Robust (14+ observations)" if has_seasonality else "Baseline Trend",
                }
            })

        return predictions
