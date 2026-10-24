from typing import List, Dict, Any
import pandas as pd
from app.services.analyst_service import AnalystService


class Forecaster:
    """Validated daily forecasting; no invented dates or single-point ranges."""
    @classmethod
    def forecast_kpi(cls,*args,**kwargs):
        if len(args)>=2:
            history=[{'value':v,'timestamp':t} for v,t in zip(args[0],args[1])]
        else:
            history=args[0] if args else kwargs.get('history',[])
        if not history or not isinstance(history[0],dict):return []
        try:
            df=pd.DataFrame(history)
            result=AnalystService(df).trend('value','timestamp',kwargs.get('horizon_days',7))
        except (ValueError,TypeError,KeyError):return []
        return [{'forecast_date':pd.Timestamp(p['date']).to_pydatetime(),'predicted_value':p['value'],
                 'range_low':p['low'],'range_high':p['high'],'confidence_level':'empirical',
                 'method':result['method'],'model_details':{'historical_samples':len(history),
                    'backtest_mae':result['backtest_mae'],'validation_observations':result['validation_observations'],
                    'limitations':result['notes']}} for p in result['forecast']]
