from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.root_cause_result import RootCauseResult
from app.repositories.base_repository import BaseRepository


class RootCauseRepository(BaseRepository[RootCauseResult]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(RootCauseResult, db, tenant_id=tenant_id)

    def get_by_detection(self, detection_id: int) -> List[RootCauseResult]:
        return (
            self._tenant_query()
            .filter(RootCauseResult.detection_id == detection_id)
            .order_by(desc(RootCauseResult.contribution_percentage))
            .all()
        )
