from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.prediction import Prediction
from app.models.kpi_definition import KPIDefinition
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.kpi_repository import KPIRepository
from app.ml.prediction.forecaster import Forecaster
from app.core.exceptions import ResourceNotFoundException


class PredictionService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.prediction_repo = PredictionRepository(db, tenant_id=tenant_id)
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)

    def generate_forecasts(self, horizon_days: int = 7) -> List[Prediction]:
        """
        Generates forward forecasts with lower & upper confidence ranges
        for all active company KPIs using actual observed business data.
        """
        active_kpis = self.kpi_repo.get_active_kpis()
        generated: List[Prediction] = []

        for kpi in active_kpis:
            history = self.kpi_repo.get_kpi_values(kpi.id, limit=200)
            if not history:
                continue

            values = [float(h.value) for h in history]
            timestamps = [h.timestamp for h in history]

            forecast_points = Forecaster.forecast_kpi(values, timestamps, horizon_days=horizon_days)
            if not forecast_points:
                continue

            # Clean up old predictions for this KPI to keep fresh
            self.db.query(Prediction).filter(
                Prediction.company_id == self.tenant_id,
                Prediction.kpi_id == kpi.id
            ).delete()

            for fp in forecast_points:
                pred = Prediction(
                    company_id=self.tenant_id,
                    kpi_id=kpi.id,
                    forecast_date=fp["forecast_date"],
                    predicted_value=float(fp["predicted_value"]) if fp["predicted_value"] is not None else 0.0,
                    range_low=float(fp["range_low"]) if fp["range_low"] is not None else 0.0,
                    range_high=float(fp["range_high"]) if fp["range_high"] is not None else 0.0,
                    confidence_level=str(fp.get("confidence_level", "moderate")),
                    method=str(fp["method"]),
                    model_details=fp.get("model_details")
                )
                self.db.add(pred)
                generated.append(pred)

        self.db.commit()

        return generated

    def get_predictions_for_kpi(self, kpi_id: int, horizon_days: int = 7) -> List[Prediction]:
        """
        Retrieves or dynamically computes real-time predictions for the specified KPI and horizon.
        Always synchronizes with current historical values for maximum accuracy.
        """
        kpi = self.kpi_repo.get_by_id(kpi_id)
        if not kpi:
            return []

        history = self.kpi_repo.get_kpi_values(kpi_id, limit=200)
        if not history:
            return []

        values = [float(h.value) for h in history]
        timestamps = [h.timestamp for h in history]

        forecast_points = Forecaster.forecast_kpi(values, timestamps, horizon_days=horizon_days)

        # Clear and replace predictions for this KPI
        self.db.query(Prediction).filter(
            Prediction.company_id == self.tenant_id,
            Prediction.kpi_id == kpi_id
        ).delete()

        fresh_preds: List[Prediction] = []
        for fp in forecast_points:
            pred = Prediction(
                company_id=self.tenant_id,
                kpi_id=kpi_id,
                forecast_date=fp["forecast_date"],
                predicted_value=float(fp["predicted_value"]) if fp["predicted_value"] is not None else 0.0,
                range_low=float(fp["range_low"]) if fp["range_low"] is not None else 0.0,
                range_high=float(fp["range_high"]) if fp["range_high"] is not None else 0.0,
                confidence_level=str(fp.get("confidence_level", "moderate")),
                method=str(fp["method"]),

                model_details=fp.get("model_details")
            )
            self.db.add(pred)
            fresh_preds.append(pred)

        self.db.commit()
        return fresh_preds


    def list_all_predictions(self) -> List[Prediction]:
        return self.prediction_repo.get_all(order_by_col="forecast_date", ascending=True)
