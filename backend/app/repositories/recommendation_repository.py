from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.recommendation import Recommendation
from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(Recommendation, db, tenant_id=tenant_id)

    def get_active_recommendations(self, limit: int = 50) -> List[Recommendation]:
        return (
            self._tenant_query()
            .filter(Recommendation.status.in_(["open", "in_progress"]))
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
            .all()
        )

    def get_by_kpi(self, kpi_id: int) -> List[Recommendation]:
        return (
            self._tenant_query()
            .filter(Recommendation.kpi_id == kpi_id)
            .order_by(desc(Recommendation.created_at))
            .all()
        )
