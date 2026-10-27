from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.recommendation import Recommendation
from app.models.detection_event import DetectionEvent
from app.models.prediction import Prediction
from app.models.kpi_definition import KPIDefinition
from app.models.company import Company
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.detection_repository import DetectionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.kpi_repository import KPIRepository
from app.core.exceptions import ResourceNotFoundException


class RecommendationService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.rec_repo = RecommendationRepository(db, tenant_id=tenant_id)
        self.detection_repo = DetectionRepository(db, tenant_id=tenant_id)
        self.prediction_repo = PredictionRepository(db, tenant_id=tenant_id)
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)

    def generate_recommendations(self) -> List[Recommendation]:
        """
        Synthesizes active detections, root causes, and forward predictions
        into concrete, practical operational recommendations explained in plain English.
        """
        detections = self.detection_repo.get_active_detections(limit=10)
        company = self.db.query(Company).filter(Company.id == self.tenant_id).first()
        industry = company.industry if company else "Retail/E-commerce"

        generated: List[Recommendation] = []

        # 1. Generate Recommendations from Detections + Root Causes
        for det in detections:
            kpi = self.kpi_repo.get_by_id(det.kpi_id)
            kpi_name = kpi.name if kpi else "Key Metric"
            
            # Check root causes
            root_causes = det.root_causes
            top_dimension_info = ""
            top_driver_name = ""
            if root_causes:
                top_rc = root_causes[0]
                top_dimension_info = f" (specifically within {top_rc.dimension_name}: {top_rc.dimension_value})"
                top_driver_name = f"{top_rc.dimension_value}"

            # Avoid duplicate open recommendation for the same detection
            existing = self.db.query(Recommendation).filter(
                Recommendation.company_id == self.tenant_id,
                Recommendation.detection_id == det.id
            ).first()
            if existing:
                continue

            title = f"Investigate {kpi_name}: {det.percentage_change:+.1f}% versus baseline"
            action = (f"Check data completeness, then review the underlying records{top_dimension_info}. "
                      "Assign an owner, state a testable explanation and measure the outcome before making operational changes.")
            category = 'analysis'
            impact = 'unestimated'
            priority = 'urgent' if det.severity == 'critical' else 'standard'
            rationale = (f"Observed {kpi_name}: {det.current_value:,.2f}; comparison baseline: {det.baseline_value:,.2f}. "
                         "This is a rule-based investigation suggestion. Financial impact and causal explanation have not been established.")

            rec = Recommendation(
                company_id=self.tenant_id,
                kpi_id=det.kpi_id,
                detection_id=det.id,
                title=title,
                action_text=action,
                rationale=rationale,
                impact_level=impact,
                priority=priority,
                category=category,
                status="open"
            )
            self.db.add(rec)
            generated.append(rec)

        (self.db.flush() if self.db.info.get("dataset_transaction") else self.db.commit())
        return generated

    def list_recommendations(self, limit: int = 50, open_only: bool = False) -> List[Recommendation]:
        recs = self.rec_repo.get_active_recommendations(limit=limit) if open_only else self.rec_repo.get_all(limit=limit)
        return recs

    def update_status(self, recommendation_id: int, new_status: str) -> Recommendation:
        rec = self.rec_repo.get_by_id(recommendation_id)
        if not rec:
            raise ResourceNotFoundException("Recommendation")
        rec.status = new_status
        (self.db.flush() if self.db.info.get("dataset_transaction") else self.db.commit())
        self.db.refresh(rec)
        return rec
