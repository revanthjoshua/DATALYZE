from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository


class NotificationService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.alert_repo = AlertRepository(db, tenant_id=tenant_id)

    def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        kpi_id: Optional[int] = None,
        detection_id: Optional[int] = None,
        recommendation_id: Optional[int] = None
    ) -> Alert:
        alert = Alert(
            company_id=self.tenant_id,
            title=title,
            message=message,
            severity=severity,
            kpi_id=kpi_id,
            detection_id=detection_id,
            recommendation_id=recommendation_id,
            is_read=False
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_alerts(self, unread_only: bool = False, limit: int = 50) -> List[Alert]:
        if unread_only:
            return self.alert_repo.get_unread_alerts(limit=limit)
        return self.alert_repo.get_all(limit=limit)

    def mark_all_read(self) -> int:
        return self.alert_repo.mark_all_as_read()
