from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.detection_event import DetectionEvent
from app.repositories.base_repository import BaseRepository


class DetectionRepository(BaseRepository[DetectionEvent]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(DetectionEvent, db, tenant_id=tenant_id)

    def get_all_detections(self, limit: int = 100, active_only: bool = False) -> List[DetectionEvent]:
        q = self._tenant_query()
        if active_only:
            q = q.filter(DetectionEvent.status == "active")
        return q.order_by(desc(DetectionEvent.detected_at)).limit(limit).all()

    def get_active_detections(self, limit: int = 50) -> List[DetectionEvent]:
        return self.get_all_detections(limit=limit, active_only=True)

    def get_detections_by_kpi(self, kpi_id: int, limit: int = 20) -> List[DetectionEvent]:
        return (
            self._tenant_query()
            .filter(DetectionEvent.kpi_id == kpi_id)
            .order_by(desc(DetectionEvent.detected_at))
            .limit(limit)
            .all()
        )
