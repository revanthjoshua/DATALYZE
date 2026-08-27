from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.detection_event import DetectionEvent
from app.models.kpi_definition import KPIDefinition
from app.models.alert import Alert
from app.repositories.detection_repository import DetectionRepository
from app.repositories.kpi_repository import KPIRepository
from app.ml.detection.anomaly_detector import AnomalyDetector
from app.services.root_cause_service import RootCauseService
from app.core.exceptions import ResourceNotFoundException


class DetectionService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.detection_repo = DetectionRepository(db, tenant_id=tenant_id)
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)
        self.root_cause_service = RootCauseService(db, tenant_id=tenant_id)

    def run_detection_pipeline(self) -> List[DetectionEvent]:
        """
        Executes statistical anomaly detection over all active company KPIs.
        For flagged anomalies, automatically runs Root Cause dimension analysis
        and creates linked in-app alerts.
        """
        active_kpis = self.kpi_repo.get_active_kpis()
        new_detections: List[DetectionEvent] = []

        for kpi in active_kpis:
            history = self.kpi_repo.get_kpi_values(kpi.id, limit=60)
            if len(history) < 4:
                continue

            values = [h.value for h in history]
            timestamps = [h.timestamp for h in history]

            result = AnomalyDetector.detect_anomalies(values, timestamps)
            if result:
                # Create Detection record
                detection = DetectionEvent(
                    company_id=self.tenant_id,
                    kpi_id=kpi.id,
                    detected_at=result["detected_at"],
                    direction=str(result["direction"]),
                    magnitude=float(result["magnitude"]) if result["magnitude"] is not None else 0.0,
                    percentage_change=float(result["percentage_change"]) if result["percentage_change"] is not None else 0.0,
                    baseline_value=float(result["baseline_value"]) if result["baseline_value"] is not None else 0.0,
                    current_value=float(result["current_value"]) if result["current_value"] is not None else 0.0,
                    severity=str(result["severity"]),
                    status="active"
                )
                self.db.add(detection)
                self.db.commit()

                self.db.refresh(detection)

                # Trigger Root-Cause Analysis immediately
                self.root_cause_service.explain_detection(detection)

                # Trigger in-app Alert
                direction_verb = "increased" if result["direction"] == "up" else "decreased"
                alert_title = f"{kpi.name} Anomaly: {abs(result['percentage_change']):.1f}% {direction_verb}"
                alert_msg = (
                    f"Measured value of {result['current_value']} diverged significantly "
                    f"from the 7-day historical baseline of {result['baseline_value']}."
                )
                alert = Alert(
                    company_id=self.tenant_id,
                    kpi_id=kpi.id,
                    detection_id=detection.id,
                    title=alert_title,
                    message=alert_msg,
                    severity="critical" if result["severity"] == "critical" else "warning",
                    is_read=False
                )
                self.db.add(alert)
                self.db.commit()

                new_detections.append(detection)

        return new_detections

    def list_detections(self, limit: int = 100, active_only: bool = False) -> List[DetectionEvent]:
        detections = self.detection_repo.get_all_detections(limit=limit, active_only=active_only)
        if not detections and not active_only:
            # Auto-run detection pipeline over active KPIs
            self.run_detection_pipeline()
            detections = self.detection_repo.get_all_detections(limit=limit, active_only=active_only)
        return detections

    def list_active_detections(self, limit: int = 50) -> List[DetectionEvent]:
        return self.list_detections(limit=limit, active_only=False)

    def acknowledge_detection(self, detection_id: int) -> DetectionEvent:
        detection = self.detection_repo.get_by_id(detection_id)
        if not detection:
            raise ResourceNotFoundException("Detection Event")
        detection.status = "acknowledged"
        self.db.commit()
        self.db.refresh(detection)
        return detection

    def acknowledge_all_detections(self) -> int:
        """Acknowledges all active detections for this workspace"""
        active = (
            self.db.query(DetectionEvent)
            .filter(DetectionEvent.company_id == self.tenant_id, DetectionEvent.status == "active")
            .all()
        )
        for det in active:
            det.status = "acknowledged"
        self.db.commit()
        return len(active)

    def create_test_anomaly(self) -> DetectionEvent:
        """Injects a simulated high-divergence anomaly event for UI layout verification"""
        kpis = self.kpi_repo.get_active_kpis()
        target_kpi = kpis[0] if kpis else None
        
        if not target_kpi:
            # Fallback KPI
            target_kpi = KPIDefinition(
                company_id=self.tenant_id,
                key="revenue",
                name="Net Revenue",
                category="Financial",
                unit="currency",
                direction="increase_is_good",
                is_active=True
            )
            self.db.add(target_kpi)
            self.db.commit()
            self.db.refresh(target_kpi)

        now = datetime.now(timezone.utc)
        test_det = DetectionEvent(
            company_id=self.tenant_id,
            kpi_id=target_kpi.id,
            detected_at=now,
            direction="down",
            magnitude=2.85,
            percentage_change=-24.6,
            baseline_value=12500.0,
            current_value=9425.0,
            severity="critical",
            status="active"
        )
        self.db.add(test_det)
        self.db.commit()
        self.db.refresh(test_det)

        # Trigger root-cause
        self.root_cause_service.explain_detection(test_det)

        # Add linked alert
        alert = Alert(
            company_id=self.tenant_id,
            kpi_id=target_kpi.id,
            detection_id=test_det.id,
            title=f"{target_kpi.name} Critical Outlier Divergence (-24.6%)",
            message=f"Measured value of 9,425 diverged by 2.85 standard deviations from baseline (12,500).",
            severity="critical",
            is_read=False
        )
        self.db.add(alert)
        self.db.commit()

        return test_det
