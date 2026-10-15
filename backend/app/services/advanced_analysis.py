"""Bounded transformations and explicit observational diagnostics."""
import numpy as np
import pandas as pd


def preparation_step(service, frame, step):
    op, col = step['operation'], step.get('column')
    if op in ['rename','derive','date_part']:
        output = step.get('value') if op=='rename' else step.get('output')
        if not isinstance(output,str) or not output.strip() or output.startswith('_') or len(output)>120 or output in frame:
            raise ValueError('Choose a new, nonempty column name (up to 120 characters, without a leading underscore).')
    if op=='rename':frame=frame.rename(columns={col:output})
    elif op=='drop_column':
        if len(frame.columns)<2:raise ValueError('Keep at least one column.')
        frame=frame.drop(columns=col)
    elif op=='derive':frame[output]=type(service)(frame)._formula_series(step.get('expression',''))
    elif op=='date_part':
        dates=service._dates(frame[col]);part=step.get('part','month')
        if part not in ['year','quarter','month','week','weekday','day']:raise ValueError('Choose a supported date part.')
        frame[output]=dates.dt.isocalendar().week if part=='week' else getattr(dates.dt,part)
    elif op=='sort':
        if step.get('direction','asc') not in ['asc','desc']:raise ValueError('Sort direction must be asc or desc.')
        frame=frame.sort_values(col,ascending=step.get('direction','asc')=='asc',kind='stable',na_position='last')
    elif op in ['lower','upper']:
        frame[col]=frame[col].map(lambda value:getattr(value,op)() if isinstance(value,str) else value)
    elif op=='replace':
        old,target=step.get('value'),step.get('target')
        if not isinstance(old,str) or not old or not isinstance(target,str):raise ValueError('Enter nonempty literal search text and replacement text.')
        frame[col]=frame[col].map(lambda value:value.replace(old,target) if isinstance(value,str) else value)
    elif op=='filter':
        operator,value=step.get('operator','eq'),step.get('value');series=frame[col]
        if operator in ['gt','gte','lt','lte']:
            values=pd.to_numeric(series,errors='coerce').replace([np.inf,-np.inf],np.nan)
            try:threshold=float(value)
            except (TypeError,ValueError):raise ValueError('Ordered filters require a finite numeric value.')
            if not np.isfinite(threshold):raise ValueError('Ordered filters require a finite numeric value.')
            mask=getattr(values,{'gt':'gt','gte':'ge','lt':'lt','lte':'le'}[operator])(threshold)
        elif operator in ['in','not_in']:
            if not isinstance(value,list) or len(value)>100:raise ValueError('List filters support at most 100 values.')
            mask=series.astype(str).isin([str(v) for v in value])
            if operator=='not_in':mask=~mask
        elif operator in ['eq','ne']:
            mask=series.astype(str).eq(str(value))
            if operator=='ne':mask=~mask
        elif operator in ['contains','starts_with','ends_with']:
            text=series.astype('string')
            mask=text.str.contains(str(value),regex=False,na=False) if operator=='contains' else getattr(text.str,{'starts_with':'startswith','ends_with':'endswith'}[operator])(str(value),na=False)
        else:raise ValueError('Choose a supported filter comparison.')
        frame=frame[mask & series.notna()]
    else:raise ValueError(f'Unsupported preparation operation: {op}')
    return frame


def validated_join(left,right,left_key,right_key,how='left',cardinality='many_to_one'):
    if how not in ['left','inner','outer']:raise ValueError('Choose left, inner or outer join.')
    if cardinality not in ['many_to_one','one_to_one','one_to_many','many_to_many']:raise ValueError('Choose an explicit key relationship.')
    lk=[left_key] if isinstance(left_key,str) else left_key
    rk=[right_key] if isinstance(right_key,str) else right_key
    if not isinstance(lk,list) or not isinstance(rk,list) or not 1<=len(lk)==len(rk)<=5 or len(set(lk))!=len(lk) or len(set(rk))!=len(rk):
        raise ValueError('Choose one to five distinct keys on each side, in matching order.')
    if any(k not in left for k in lk) or any(k not in right for k in rk):raise ValueError('The selected join keys must exist in their datasets.')
    if max(len(left),len(right))>100000 or left.empty or right.empty:raise ValueError('Each dataset must contain 1–100,000 rows.')
    if left[lk].isna().any().any() or right[rk].isna().any().any():raise ValueError('Join keys must be nonmissing; prepare missing keys explicitly first.')
    if cardinality in ['many_to_one','one_to_one'] and right.duplicated(rk).any():raise ValueError('The lookup key must be unique for this key relationship.')
    if cardinality in ['one_to_many','one_to_one'] and left.duplicated(lk).any():raise ValueError('The active key must be unique for this key relationship.')
    a=left.groupby(lk,dropna=False,observed=True).size().to_dict()
    b=right.groupby(rk,dropna=False,observed=True).size().to_dict()
    matched=sum(int(count)*int(b.get(key,0)) for key,count in a.items())
    unmatched_left=sum(int(count) for key,count in a.items() if key not in b)
    unmatched_right=sum(int(count) for key,count in b.items() if key not in a)
    expected=matched+(unmatched_left if how in ['left','outer'] else 0)+(unmatched_right if how=='outer' else 0)
    if not 1<=expected<=100000:raise ValueError('Join must produce between 1 and 100,000 rows. Refine keys before joining.')
    result=left.merge(right,left_on=lk,right_on=rk,how=how,validate=cardinality,suffixes=('','_lookup'))
    if not result.columns.is_unique:raise ValueError('Join would create duplicate column names. Rename overlapping columns first.')
    if len(result)!=expected:raise ValueError('Join key types are incompatible; convert them explicitly before joining.')
    return result,{'rows_before':len(left),'rows_after':len(result),'matched_rows':matched,
        'unmatched_source_rows':unmatched_left,'unmatched_lookup_rows':unmatched_right,
        'expansion_factor':round(len(result)/len(left),4),'cardinality':cardinality}


def forecast(service,metric,date_column,horizon):
    from app.services.analyst_service import records
    if type(horizon) is not int or not 1<=horizon<=30:raise ValueError('Horizon must be between 1 and 30 days.')
    dates=service._dates(service.column(date_column))
    work=pd.DataFrame({'date':dates.dt.floor('D'),'value':service.column(metric,True)}).dropna()
    daily=work.groupby('date').value.sum(min_count=1).sort_index()
    if len(daily)<12:raise ValueError('At least 12 dated daily observations are required for a validated forecast.')
    if not (daily.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all():raise ValueError('Daily observations contain calendar gaps. Resolve missing days explicitly before forecasting.')
    values=daily.to_numpy(dtype=float)
    methods=['Last observed value','Recent mean','Linear trend']
    if len(values)>=28:methods+=['Weekly seasonal']
    def predict(history,count,method):
        if method=='Last observed value':return np.repeat(history[-1],count)
        if method=='Recent mean':return np.repeat(np.mean(history[-7:]),count)
        if method=='Weekly seasonal':return np.resize(history[-7:],count)
        slope,intercept=np.polyfit(np.arange(len(history)),history,1)
        return intercept+slope*np.arange(len(history),len(history)+count)
    holdout=min(28,max(3,len(values)//4));start=max(7,len(values)-holdout)
    errors={};residuals={};horizon_errors={}
    for model in methods:
        by_horizon={h:[] for h in range(1,horizon+1)}
        for origin in range(start,len(values)):
            count=min(horizon,len(values)-origin)
            predicted=predict(values[:origin],count,model)
            for h in range(count):by_horizon[h+1].append(float(values[origin+h]-predicted[h]))
        horizon_errors[model]=by_horizon
        residuals[model]=by_horizon[1]
        # Equal weight per supported horizon avoids over-weighting short horizons.
        errors[model]=float(np.mean([np.mean(np.abs(v)) for v in by_horizon.values() if v]))
    chosen=min(errors,key=errors.get);predictions=predict(values,horizon,chosen)
    points=[];validation=[]
    one_step_spread=float(np.quantile(np.abs(residuals[chosen]),.95))
    for h,value in enumerate(predictions,1):
        observed=horizon_errors[chosen][h]
        spread=float(np.quantile(np.abs(observed),.95)) if len(observed)>=3 else one_step_spread*np.sqrt(h)
        points.append({'date':(daily.index[-1]+pd.Timedelta(days=h)).isoformat(),'value':float(value),
            'low':float(value-spread),'high':float(value+spread),'validation_samples':len(observed)})
        validation.append({'horizon_days':h,'samples':len(observed),'mae':float(np.mean(np.abs(observed))) if observed else None,
            'range_method':'Observed horizon residuals' if len(observed)>=3 else 'Sparse validation: scaled one-step residuals'})
    history=daily.rename('value').to_frame();history['moving_average_7']=daily.rolling(7,min_periods=3).mean()
    prior_mean=daily.shift().rolling(7,min_periods=5).mean();prior_std=daily.shift().rolling(7,min_periods=5).std()
    history['anomaly']=((daily-prior_mean).abs()>3*prior_std)&prior_std.notna()
    return {'method':chosen,'backtest_mae':errors,'validation_observations':len(residuals[chosen]),
        'validation_by_horizon':validation,'excluded_rows':len(service.frame)-len(work),'history':records(history.reset_index()),'forecast':points,
        'notes':['Daily totals; candidate models are compared using rolling-origin forecasts across the requested horizon. Weekly seasonality is tested when at least 28 consecutive days exist.',
        'Forecast ranges use observed absolute validation errors by horizon when at least three exist; otherwise they scale one-step errors. These are empirical ranges, not guaranteed 95% coverage.',
        'Future external events and structural changes are not modeled. Inspect validation sample counts before using long-range forecasts.',
        'Anomaly signals compare each day with the previous seven days; they require investigation.']}


def investigate(service,metric,date_column,dimension,split_date,baseline_start_date=None,comparison_end_date=None,filters=None):
    from app.services.analyst_service import records
    frame=service.frame
    if filters:
        if not isinstance(filters,dict) or len(filters)>5:raise ValueError('Drilldown supports up to five exact column/value filters.')
        for column,value in filters.items():
            if column not in frame:raise ValueError('Unknown drilldown column.')
            frame=frame[frame[column].astype(str).eq(str(value))]
    filtered=type(service)(frame)
    dates=filtered._dates(filtered.column(date_column));values=filtered.column(metric,True)
    split=pd.to_datetime(split_date,utc=True)
    if pd.isna(split) or split!=split.floor('D'):raise ValueError('Provide a split date at midnight UTC.')
    work=pd.DataFrame({'date':dates.dt.floor('D'),'value':values,'segment':filtered.column(dimension).fillna('(missing)').astype(str)}).dropna(subset=['date','value'])
    start=pd.to_datetime(baseline_start_date,utc=True) if baseline_start_date else None
    end=pd.to_datetime(comparison_end_date,utc=True) if comparison_end_date else None
    if start is not None:
        if pd.isna(start) or start>=split:raise ValueError('Baseline start must be before the comparison period.')
        work=work[work.date>=start.floor('D')]
    if end is not None:
        if pd.isna(end) or end<split:raise ValueError('Comparison end must be on or after the split date.')
        work=work[work.date<=end.floor('D')]
    before=work[work.date<split];after=work[work.date>=split]
    nb,na=before.date.nunique(),after.date.nunique()
    if min(nb,na)<1:raise ValueError('Both periods need dated observations.')
    result=pd.DataFrame({'baseline_per_observed_day':before.groupby('segment').value.sum()/nb,
                         'comparison_per_observed_day':after.groupby('segment').value.sum()/na}).fillna(0)
    result['change']=result.comparison_per_observed_day-result.baseline_per_observed_day
    result['baseline_rows_per_day']=before.groupby('segment').size().reindex(result.index,fill_value=0)/nb
    result['comparison_rows_per_day']=after.groupby('segment').size().reindex(result.index,fill_value=0)/na
    result['baseline_mean_per_row']=before.groupby('segment').value.mean().reindex(result.index)
    result['comparison_mean_per_row']=after.groupby('segment').value.mean().reindex(result.index)
    # Symmetric count/mean decomposition reconciles for segments present in both periods.
    result['row_volume_component']=(result.comparison_rows_per_day-result.baseline_rows_per_day)*(result.baseline_mean_per_row+result.comparison_mean_per_row)/2
    result['row_value_component']=(result.comparison_mean_per_row-result.baseline_mean_per_row)*(result.baseline_rows_per_day+result.comparison_rows_per_day)/2
    result['entry_exit_component']=result['change'].where(result.baseline_mean_per_row.isna()|result.comparison_mean_per_row.isna(),0)
    result=result.reindex(result.change.abs().sort_values(ascending=False).index)
    total=float(result.change.sum());result['share_of_net_change_pct']=result.change/total*100 if abs(total)>1e-12 else np.nan
    coverage=[]
    for name,part,days,bound_start,bound_end in [('Baseline',before,nb,start,split-pd.Timedelta(days=1)),('Comparison',after,na,split,end)]:
        low=bound_start if bound_start is not None else part.date.min()
        high=bound_end if bound_end is not None else part.date.max()
        calendar=max(1,(high.floor('D')-low.floor('D')).days+1)
        coverage.append({'period':name,'rows':len(part),'observed_days':int(days),'calendar_days':calendar,'missing_calendar_days':int(calendar-days)})
    return {'method':'Additive segment contribution with row-volume and row-value decomposition','rows':records(result.rename_axis('segment').reset_index()),
        'net_change':total,'excluded_rows':len(service.frame)-len(work),'baseline_observed_days':int(nb),'comparison_observed_days':int(na),'coverage':coverage,
        'filters':filters or {},'notes':['Contributions identify where the measured change occurred; they do not establish its cause.',
        'Totals are normalized by observed days. Missing calendar days are reported and are not assumed to contain zero activity.',
        'Row-volume and mean-per-row components use a symmetric decomposition. Rows represent transactions only if the source is at that grain. New or disappearing segments are reported separately.',
        'Negative offsets can make shares exceed 100%. Validate coverage, collection changes and proposed explanations with business owners.'],
        'recommended_next_steps':['Check coverage and source-grain consistency before acting.','Drill into the largest segment and record a testable explanation.','Assign an owner and validation measure, then review the outcome in Share.']}
