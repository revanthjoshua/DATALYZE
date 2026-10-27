from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.detection_event import DetectionEvent
from app.models.root_cause_result import RootCauseResult
from app.models.kpi_definition import KPIDefinition
from app.repositories.root_cause_repository import RootCauseRepository
from app.repositories.kpi_repository import KPIRepository
from app.ml.root_cause.contribution_analyzer import ContributionAnalyzer
from app.services.dataset_store import TenantDatasetStore


class RootCauseService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = RootCauseRepository(db, tenant_id=tenant_id)
        self.kpi_repo = KPIRepository(db, tenant_id=tenant_id)

    def explain_detection(self, detection: DetectionEvent) -> List[RootCauseResult]:
        """
        Analyzes contributing dimensions for a detected anomaly and persists mathematically normalized root causes.
        """
        kpi = self.kpi_repo.get_by_id(detection.kpi_id)
        kpi_name = kpi.name if kpi else "Key Metric"
        kpi_key = kpi.key if kpi else "metric"

        # Contributions require observed dates and explicit comparison windows.
        # Missing dimensional evidence must remain unknown, never a domain fallback.
        import pandas as pd
        from app.services.analyst_service import AnalystService
        from app.api.v1.data_routes import _ensure_dataset_loaded
        contributions = []
        df = _ensure_dataset_loaded(self.tenant_id, self.db)
        if df is not None and not df.empty and kpi_key in df:
            date_col = '_parsed_date' if '_parsed_date' in df else next(
                (c for c in df if c.lower() in ['date','timestamp','order_date','transaction_date']), None)
            if date_col:
                dates = pd.to_datetime(df[date_col], errors='coerce', utc=True)
                split = pd.Timestamp(detection.detected_at)
                split = split.tz_localize('UTC') if split.tzinfo is None else split.tz_convert('UTC')
                split = split.floor('D')
                window = df[(dates >= split-pd.Timedelta(days=7)) & (dates < split+pd.Timedelta(days=1))].copy()
                window['observed_date'] = dates.loc[window.index]
                dimensions = [c for c in window.select_dtypes(include=['object','category','string'])
                              if c != date_col and ContributionAnalyzer.is_valid_business_dimension(c)
                              and 1 < window[c].nunique() <= 30]
                if dimensions:
                    dim = dimensions[0]
                    try:
                        result = AnalystService(window).investigate(kpi_key,'observed_date',dim,split.isoformat())
                        for item in result['rows']:
                            pct = item['share_of_net_change_pct']
                            if pct is None: continue
                            contributions.append({'dimension_name':dim,'dimension_value':item['segment'],
                                'contribution_percentage':pct,'confidence_score':None,
                                'explanation_text':f"{item['segment']}: mean daily {kpi_name} changed by {item['change']:.4g}, comparing the detection day with observed days in the preceding week. This is a segment contribution, not proof of cause."})
                    except (ValueError,TypeError,KeyError):
                        pass

        # Clean existing root cause results for this detection
        self.db.query(RootCauseResult).filter(
            RootCauseResult.company_id == self.tenant_id,
            RootCauseResult.detection_id == detection.id
        ).delete()

        persisted: List[RootCauseResult] = []
        for c in contributions:
            rc = RootCauseResult(
                company_id=self.tenant_id,
                detection_id=detection.id,
                dimension_name=str(c["dimension_name"]),
                dimension_value=str(c["dimension_value"]),
                contribution_percentage=float(c["contribution_percentage"]) if c["contribution_percentage"] is not None else 0.0,
                explanation_text=str(c["explanation_text"]),
                confidence_score=None
            )
            self.db.add(rc)
            persisted.append(rc)

        (self.db.flush() if self.db.info.get("dataset_transaction") else self.db.commit())

        return persisted

    def get_root_causes_for_detection(self, detection_id: int) -> List[RootCauseResult]:
        return self.repo.get_by_detection(detection_id)
