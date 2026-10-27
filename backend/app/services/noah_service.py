"""Rule-based lookup of recorded dataset facts. No autonomous actions or model claims."""
from datetime import datetime, timezone
from app.schemas.noah_schema import NoahQueryResponse, NoahDataReference
from app.services.dataset_store import TenantDatasetStore
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService
from app.repositories.detection_repository import DetectionRepository
from app.repositories.kpi_repository import KPIRepository


class NoahService:
    def __init__(self, db, tenant_id):
        self.db=db
        self.tenant_id=tenant_id

    def process_query(self, request):
        from app.api.v1.data_routes import _ensure_dataset_loaded
        _ensure_dataset_loaded(self.tenant_id,self.db)
        meta=TenantDatasetStore.get_metadata(self.tenant_id)
        q=request.question.strip()
        lower=q.lower()
        references=[]
        actions=['Show uploaded columns','Show total revenue','Show saved forecasts']
        lines=[]
        if not meta:
            lines=['No active dataset is available. Upload data before asking for measurements. Use Analyst Workspace to define the question and intended decision.']
        elif any(w in lower for w in ['predict','forecast']):
            rows=PredictionService(self.db,self.tenant_id).list_all_predictions()
            names={k.id:k.name for k in KPIRepository(self.db,self.tenant_id).get_active_kpis()}
            lines=['Saved forecast observations (first 7 points):'] if rows else ['No validated forecast is saved. Forecasting requires at least 12 consecutive daily observations; use Investigate in Analyst Workspace.']
            for r in rows[:7]:
                name=names.get(r.kpi_id,'Metric')
                lines.append(f'{name}, {r.forecast_date.date()}: {r.predicted_value:,.2f}; empirical range {r.range_low:,.2f} to {r.range_high:,.2f}.')
                references.append(NoahDataReference(source_type='prediction',title=name,value=str(r.predicted_value)))
            if rows: lines.append('Models are compared by rolling validation error. These ranges are not calibrated confidence guarantees.')
        elif any(w in lower for w in ['why','cause','anomal','drop','spike']):
            rows=DetectionRepository(self.db,self.tenant_id).get_active_detections(limit=5)
            lines=['Recorded anomaly signals:'] if rows else ['No active anomaly signals are recorded. This does not establish that all data or business outcomes are healthy.']
            for r in rows:
                lines.append(f'Observed {r.current_value:,.2f}; comparison baseline {r.baseline_value:,.2f}; change {r.percentage_change:+.2f}%.')
                references.append(NoahDataReference(source_type='detection',title=f'Signal #{r.id}',value=str(r.current_value)))
                for cause in r.root_causes[:3]: lines.append(cause.explanation_text)
            lines.append('Contributions locate observed changes; causal explanations require validation. Choose a dimension and period under Investigate.')
        elif any(w in lower for w in ['recommend','action','next step']):
            rows=RecommendationService(self.db,self.tenant_id).list_recommendations()
            lines=['Recorded investigation suggestions:'] if rows else ['No investigation suggestions are saved. Review data quality and define a question before choosing an action.']
            for r in rows[:5]:
                lines.append(f'{r.title}: {r.action_text}')
                references.append(NoahDataReference(source_type='recommendation',title=r.title,value=r.priority))
            lines.append('Record an owner, validation measure and progress under Share. Suggestions do not establish financial impact.')
        else:
            result=TenantDatasetStore.analyze_query(self.tenant_id,q)
            lines=[f"Active dataset: {meta['filename']} ({meta['row_count']:,} rows). Scope: complete active dataset."]
            references.append(NoahDataReference(source_type='dataset',title=meta['filename'],value=f"{meta['row_count']} rows",details={'revision':meta.get('revision')}))
            for m in result.get('matched_metrics',[]):
                lines.append(f"{m['display_name']}: total {m['total']:,.2f}; mean {m['average']:,.2f}; {m['count']} observed values.")
            for column,info in result.get('matched_categories',{}).items():
                lines.append(f"{column}, grouped by {info.get('metric','record count')}: "+'; '.join(f'{name}: {value}' for name,value in list(info.get('breakdown',{}).items())[:8]))
            for item in result.get('matched_values',[]):
                lines.append(f"Segment {item['value']} in {item['column']}: {item['row_count']} rows; "+'; '.join(f'{name}: {value}' for name,value in item.get('metrics',{}).items()))
            if len(lines)==1: lines.append('Available columns: '+', '.join(meta['columns'])+'. Use Explore and Investigate for explicit filters, statistical tests and reproducible analysis.')
        return NoahQueryResponse(question=q,answer='\n\n'.join(lines),references=references,suggested_actions=actions,structured_data={'mode':'Rule-based dataset lookup'},timestamp=datetime.now(timezone.utc))
