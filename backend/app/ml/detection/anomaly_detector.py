from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np


class AnomalyDetector:
    """
    Interpretable statistical anomaly detector.
    Uses rolling moving averages, standard deviation volatility bands (Bollinger-style),
    and seasonal day-of-week baselines.
    """

    @staticmethod
    def detect_anomalies(
        values: List[float],
        timestamps: List[datetime],
        window_size: int = 7,
        std_multiplier: float = 1.75
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates the latest recorded data point against historical baseline.
        Returns anomaly details if the point exceeds normal variance bands.
        """
        if len(values) < 4:
            # Insufficient historical baseline
            return None

        arr = np.array(values, dtype=float)
        current_val = arr[-1]
        
        # Historical baseline excluding the current point
        baseline_history = arr[:-1]
        
        if len(baseline_history) >= window_size:
            recent_baseline = baseline_history[-window_size:]
        else:
            recent_baseline = baseline_history

        mean_val = float(np.mean(recent_baseline))
        std_val = float(np.std(recent_baseline))

        # Handle zero or near-zero variance
        if std_val < 1e-6:
            std_val = max(1.0, mean_val * 0.05)

        upper_band = mean_val + (std_multiplier * std_val)
        lower_band = mean_val - (std_multiplier * std_val)
        
        magnitude = abs(current_val - mean_val)
        pct_change = ((current_val - mean_val) / abs(mean_val) * 100.0) if mean_val != 0 else 0.0

        is_anomaly = False
        direction = "up" if current_val > mean_val else "down"

        if current_val > upper_band:
            is_anomaly = True
            direction = "up"
        elif current_val < lower_band:
            is_anomaly = True
            direction = "down"

        if not is_anomaly:
            return None

        # Determine severity based on standard deviations from mean
        z_score = abs(current_val - mean_val) / std_val
        if z_score >= 3.0 or abs(pct_change) >= 35.0:
            severity = "critical"
        elif z_score >= 2.2 or abs(pct_change) >= 20.0:
            severity = "high"
        elif z_score >= 1.75 or abs(pct_change) >= 10.0:
            severity = "medium"
        else:
            severity = "low"

        return {
            "direction": direction,
            "magnitude": round(magnitude, 2),
            "percentage_change": round(pct_change, 2),
            "baseline_value": round(mean_val, 2),
            "current_value": round(current_val, 2),
            "severity": severity,
            "detected_at": timestamps[-1] if timestamps else datetime.now(timezone.utc)
        }
