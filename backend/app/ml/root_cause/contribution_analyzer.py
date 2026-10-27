from typing import Any, Dict, List, Optional
import math
import pandas as pd
from app.services.analyst_service import AnalystService


class ContributionAnalyzer:
    """Observed contributions, with no fabricated weights or causal confidence."""
    @classmethod
    def is_valid_business_dimension(cls, name):
        return not name.startswith('_') and name.lower() not in ['id','date','timestamp','row_id','index'] and not name.lower().endswith('_id')

    @classmethod
    def analyze_from_dataset(cls, df, kpi_col, dimension_cols, direction='down', overall_change=0., kpi_name='Metric', date_col=None, split_date=None):
        if date_col is None or split_date is None:
            return []
        dimensions=[d for d in dimension_cols if d in df and cls.is_valid_business_dimension(d)]
        if not dimensions:return []
        result=AnalystService(df).investigate(kpi_col,date_col,dimensions[0],split_date)
        return [{'dimension_name':dimensions[0],'dimension_value':r['segment'],
                 'contribution_percentage':r['share_of_net_change_pct'],
                 'explanation_text':f"Mean daily {kpi_name} changed by {r['change']:.4g} in {r['segment']}. Contribution is not proof of cause.",
                 'confidence_score':None} for r in result['rows'] if r['share_of_net_change_pct'] is not None]

    @classmethod
    def analyze_dimension_contributions(cls,current_dim_data,baseline_dim_data,overall_change,direction,kpi_name='Metric'):
        if not isinstance(current_dim_data,dict) or not isinstance(baseline_dim_data,dict):return []
        for dim,current in current_dim_data.items():
            previous=baseline_dim_data.get(dim)
            if not cls.is_valid_business_dimension(dim) or not isinstance(current,dict) or not isinstance(previous,dict):continue
            keys=set(current)|set(previous)
            try:
                differences={key:float(current.get(key,0))-float(previous.get(key,0)) for key in keys}
            except (ValueError,TypeError):continue
            if not all(math.isfinite(v) for v in differences.values()):continue
            total=sum(differences.values())
            if abs(total)<1e-12:return []
            return [{'dimension_name':dim,'dimension_value':str(key),'contribution_percentage':value/total*100,
                     'explanation_text':f"Observed {kpi_name} changed by {value:.4g} in {key}. This explains a segment change, not causation.",
                     'confidence_score':None} for key,value in sorted(differences.items(),key=lambda item:abs(item[1]),reverse=True)]
        return []
