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

            if det.direction == "down":
                if "revenue" in (kpi.key if kpi else "") or "sales" in (kpi.key if kpi else ""):
                    title = f"Investigate {abs(det.percentage_change):.1f}% Revenue Decline in {kpi_name}"
                    action = (
                        f"Review campaign spend, inventory availability, and regional fulfillment channels{top_dimension_info}. "
                        f"Re-engage stalled customer segments with targeted retention incentives."
                    )
                    category = "marketing"
                    impact = "high"
                    priority = "urgent" if det.severity == "critical" else "standard"
                elif "aov" in (kpi.key if kpi else ""):
                    title = f"Introduce Product Bundling to Recover Average Order Value"
                    action = f"Deploy checkout cross-sell recommendations on top-performing items{top_dimension_info} to elevate basket size."
                    category = "pricing"
                    impact = "medium"
                    priority = "standard"
                elif "churn" in (kpi.key if kpi else ""):
                    title = f"Trigger Proactive Retention for At-Risk Customers"
                    action = f"Deploy customer success intervention outreach for accounts showing declining usage{top_dimension_info}."
                    category = "operations"
                    impact = "high"
                    priority = "urgent"
                else:
                    title = f"Address Negative Anomaly in {kpi_name}"
                    action = f"Audit operational inputs and fulfillment metrics{top_dimension_info} to stabilize variance."
                    category = "operations"
                    impact = "medium"
                    priority = "standard"
            else:
                title = f"Capitalize on {abs(det.percentage_change):.1f}% Surge in {kpi_name}"
                action = (
                    f"Increase stock allocation and marketing focus behind top contributors{top_dimension_info} "
                    f"to sustain positive demand momentum."
                )
                category = "inventory" if "Retail" in industry else "marketing"
                impact = "high"
                priority = "standard"

            # Plain-English business explanation
            direction_word = "dropped" if det.direction == "down" else "surged"
            driver_clause = f", most likely driven by '{top_driver_name}'" if top_driver_name else ""
            rationale = (
                f"This action was recommended because {kpi_name} {direction_word} "
                f"{abs(det.percentage_change):.1f}% below its baseline "
                f"(from {det.baseline_value:,.2f} to {det.current_value:,.2f}){driver_clause}."
            )

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

        # 2. If no anomaly detections exist yet, generate strategic prescriptions from active KPIs
        if not generated and not self.rec_repo.get_active_recommendations():
            active_kpis = self.kpi_repo.get_active_kpis()
            for kpi in active_kpis[:3]:
                history = self.kpi_repo.get_kpi_values(kpi.id, limit=30)
                if not history:
                    continue
                val = history[-1].value if history else 0.0

                rec = Recommendation(
                    company_id=self.tenant_id,
                    kpi_id=kpi.id,
                    title=f"Optimize Baseline Performance for {kpi.name}",
                    action_text=f"Review operational inputs and capacity planning to sustain positive {kpi.name} trajectory.",
                    rationale=f"This action was recommended to optimize {kpi.name} (currently measuring {val:,.2f}) and strengthen operational margins.",
                    impact_level="medium",
                    priority="standard",
                    category="operations",
                    status="open"
                )
                self.db.add(rec)
                generated.append(rec)

        self.db.commit()
        return generated

    def list_recommendations(self, limit: int = 50, open_only: bool = False) -> List[Recommendation]:
        recs = self.rec_repo.get_active_recommendations(limit=limit) if open_only else self.rec_repo.get_all(limit=limit)
        if not recs:
            self.generate_recommendations()
            recs = self.rec_repo.get_active_recommendations(limit=limit) if open_only else self.rec_repo.get_all(limit=limit)
        return recs

    def update_status(self, recommendation_id: int, new_status: str) -> Recommendation:
        rec = self.rec_repo.get_by_id(recommendation_id)
        if not rec:
            raise ResourceNotFoundException("Recommendation")
        rec.status = new_status
        self.db.commit()
        self.db.refresh(rec)
        return rec
