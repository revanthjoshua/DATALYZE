from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.report import Report
from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(Report, db, tenant_id=tenant_id)

    def get_recent_reports(self, limit: int = 20) -> List[Report]:
        return (
            self._tenant_query()
            .order_by(desc(Report.created_at))
            .limit(limit)
            .all()
        )
