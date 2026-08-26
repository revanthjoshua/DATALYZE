from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.prediction import Prediction
from app.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(Prediction, db, tenant_id=tenant_id)

    def get_predictions_by_kpi(self, kpi_id: int, from_date: Optional[datetime] = None) -> List[Prediction]:
        query = self._tenant_query().filter(Prediction.kpi_id == kpi_id)
        if from_date:
            query = query.filter(Prediction.forecast_date >= from_date)
        return query.order_by(asc(Prediction.forecast_date)).all()
