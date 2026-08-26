from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.alert import Alert
from app.repositories.base_repository import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(Alert, db, tenant_id=tenant_id)

    def get_unread_alerts(self, limit: int = 50) -> List[Alert]:
        return (
            self._tenant_query()
            .filter(Alert.is_read == False)
            .order_by(desc(Alert.created_at))
            .limit(limit)
            .all()
        )

    def mark_all_as_read(self) -> int:
        unread = self.get_unread_alerts(limit=500)
        for alert in unread:
            alert.is_read = True
        self.db.commit()
        return len(unread)
