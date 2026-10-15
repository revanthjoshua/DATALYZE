import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, TrendingUp } from 'lucide-react';
import { kpiApi } from '../api/kpiApi';
import { predictionApi } from '../api/predictionApi';
import { KPISummaryCard } from '../types/kpi.types';
import { Prediction } from '../types/noah.types';
import { useTenant } from '../context/TenantContext';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { EmptyState, ErrorState } from '../components/ui/StateView';
import { PredictionRangeChart } from '../components/prediction/PredictionRangeChart';

export const PredictionsPage: React.FC = () => {
  const { company } = useTenant();
  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    kpiApi.getDashboardSummary('ALL').then(data => {
      if (!active) return;
      setKpis(data);
      setSelected(current => data.some(k => k.id === current) ? current : data[0]?.id ?? null);
      if (!data.length) setLoading(false);
    }).catch(() => {
      if (active) { setError('Saved forecasts could not be loaded. Please retry.'); setLoading(false); }
    });
    return () => { active = false; };
  }, [refresh]);

  useEffect(() => {
    if (selected === null) return;
    let active = true;
    setLoading(true);
    setPredictions([]);
    setError(null);
    predictionApi.getPredictions(selected, 30).then(data => {
      if (active) setPredictions(data.slice().sort((a, b) => a.forecast_date.localeCompare(b.forecast_date)));
    }).catch(() => {
      if (active) setError('The forecast request failed. Please retry.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selected, refresh]);

  const kpi = kpis.find(k => k.id === selected);
  const details = predictions[0]?.model_details;
  return <div className="space-y-6">
    <PageHeader title="Saved Forecasts" stage="Anticipate" stageIcon={<TrendingUp className="w-4 h-4" />}
      description="Review projections saved for the current dataset. Compare model error and assumptions before using a forecast to make a decision."
      actions={<Button variant="secondary" onClick={() => setRefresh(v => v + 1)} leftIcon={<RefreshCw className="w-4 h-4" />}>Refresh saved results</Button>} />
    <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#15171C] p-5 space-y-3">
      <p className="text-sm text-neutral-600 dark:text-neutral-300">Forecasting requires at least 12 consecutive days of dated observations. Daily totals are compared using a rolling validation window. Missing dates are reported instead of filled with invented observations.</p>
      <Link to="/analysis" className="inline-block font-semibold text-sm text-[#6B4226] dark:text-[#D5B79F] underline">Open Analyst Workspace to calculate and save forecast evidence</Link>
      <p className="text-xs text-neutral-500">Workspace forecast evidence is stored in Share. This page shows the KPI forecasts generated when the dataset is processed. Refresh retrieves saved results only.</p>
    </div>
    {kpis.length > 0 && <label className="block space-y-2 text-sm font-semibold">Metric
      <select aria-label="Forecast metric" value={selected ?? ''} onChange={e => setSelected(Number(e.target.value))} className="block w-full sm:max-w-md p-3 border border-neutral-200 dark:border-neutral-700 rounded-xl bg-white dark:bg-[#15171C]">
        {kpis.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
    </label>}
    {loading ? <p role="status" className="text-sm text-neutral-500">Loading saved forecasts…</p> : error ? <ErrorState message={error} onRetry={() => setRefresh(v => v + 1)} /> : predictions.length && kpi ? <>
      <PredictionRangeChart history={kpi.recent_history} predictions={predictions} kpiName={kpi.name} unit={kpi.unit} currency={company?.currency || 'USD'} horizonDays={predictions.length} />
      <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 text-sm space-y-2">
        <p><strong>Saved:</strong> {new Date(predictions[0].created_at).toLocaleString()}</p>
        <p><strong>Method:</strong> {predictions[0].method.replace(/_/g, ' ')}</p>
        <p>The shaded range reflects empirical validation errors. It is not a calibrated 95% prediction interval; changes in the business or data can increase error.</p>
        {details && <details><summary className="cursor-pointer font-semibold">Validation evidence and assumptions</summary><pre className="text-xs mt-3 overflow-auto whitespace-pre-wrap">{JSON.stringify(details, null, 2)}</pre></details>}
      </div>
    </> : <EmptyState title="No saved forecast for this metric" description="A reliable dated series may not be available yet. In Analyst Workspace, choose a date column and a numeric measure to inspect the data and run a validated forecast." customAction={<Link to="/analysis" className="underline text-sm font-semibold">Open Analyst Workspace</Link>} />}
  </div>;
};
