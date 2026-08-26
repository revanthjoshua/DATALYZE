import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  ShieldCheck,
  Activity,
  Sparkles,
  Sliders,
  TrendingUp,
  RefreshCw,
  LineChart,
  FileSpreadsheet,
} from 'lucide-react';
import { predictionApi } from '../api/predictionApi';
import { kpiApi } from '../api/kpiApi';
import { Prediction } from '../types/noah.types';
import { KPISummaryCard } from '../types/kpi.types';
import { PredictionRangeChart } from '../components/prediction/PredictionRangeChart';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { useDateRange } from '../context/DateRangeContext';
import { formatKPIValue } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';
import { DenseTable, ColumnDef } from '../components/ui/DenseTable';

export const PredictionsPage: React.FC = () => {
  const { company } = useTenant();
  const toast = useToast();
  const navigate = useNavigate();
  const { timeRange } = useDateRange();

  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [selectedKpiId, setSelectedKpiId] = useState<number>(() => {
    const saved = localStorage.getItem('datalyze_pred_kpi_id');
    return saved ? parseInt(saved, 10) : 1;
  });
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [predLoading, setPredLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Timeframe Horizon (7, 14, 30, 90 days)
  const [forecastHorizon, setForecastHorizon] = useState<number>(7);

  // Scenario Simulation Adjustment Slider (% change)
  const [simulationMultiplier, setSimulationMultiplier] = useState<number>(0);

  // Fetch summary of all KPIs
  const fetchKpisAndData = useCallback(async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await kpiApi.getDashboardSummary();
      setKpis(data);
      if (data.length > 0) {
        const exists = data.some((k) => k.id === selectedKpiId);
        if (!exists) {
          setSelectedKpiId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load KPIs for predictions', err);
      setErrorMsg('Failed to fetch metric baselines for predictive forecasting.');
    } finally {
      setLoading(false);
    }
  }, [selectedKpiId]);

  useEffect(() => {
    fetchKpisAndData();
  }, []);

  // Fetch predictions whenever selected KPI or horizon changes
  const fetchPredictions = useCallback(
    async (horizon: number = forecastHorizon, targetKpiId: number = selectedKpiId) => {
      if (!targetKpiId) return;
      try {
        setPredLoading(true);
        const data = await predictionApi.getPredictions(targetKpiId, horizon);
        setPredictions(data);
      } catch (err) {
        console.error('Failed to load predictions', err);
        toast.error('Failed to generate predictive forecast.', 'Prediction Error');
      } finally {
        setPredLoading(false);
      }
    },
    [forecastHorizon, selectedKpiId, toast]
  );

  useEffect(() => {
    if (selectedKpiId && kpis.length > 0) {
      fetchPredictions(forecastHorizon, selectedKpiId);
    }
  }, [selectedKpiId, forecastHorizon, kpis]);

  const handleKpiSelect = (id: number) => {
    setSelectedKpiId(id);
    localStorage.setItem('datalyze_pred_kpi_id', String(id));
    fetchPredictions(forecastHorizon, id);
  };

  const handleHorizonChange = (horizon: number) => {
    setForecastHorizon(horizon);
    fetchPredictions(horizon, selectedKpiId);
    toast.info(`Recalculating forward statistical forecast for ${horizon} days...`, 'Model Recalculation');
  };

  const selectedKpi = kpis.find((k) => k.id === selectedKpiId) || (kpis.length > 0 ? kpis[0] : null);
  const currency = company?.currency || 'USD';
  const confidence = predictions.length > 0 ? predictions[0].confidence_level : 'moderate';

  // Apply scenario simulation multiplier if active
  const simulatedPredictions = predictions.map((p) => {
    const factor = 1 + simulationMultiplier / 100;
    return {
      ...p,
      predicted_value: p.predicted_value * factor,
      range_low: p.range_low !== null ? p.range_low * factor : p.predicted_value * 0.9 * factor,
      range_high: p.range_high !== null ? p.range_high * factor : p.predicted_value * 1.1 * factor,
    };
  });

  const columns: ColumnDef<Prediction>[] = [
    {
      key: 'forecast_date',
      header: 'Forecast Date',
      sortable: true,
      render: (p) => (
        <span className="font-mono text-xs text-neutral-900 dark:text-neutral-100 flex items-center space-x-1.5">
          <Calendar className="w-3.5 h-3.5 text-neutral-400" />
          <span>
            {new Date(p.forecast_date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              weekday: 'short',
              year: 'numeric',
            })}
          </span>
        </span>
      ),
    },
    {
      key: 'predicted_value',
      header: 'Expected Value',
      align: 'right',
      sortable: true,
      render: (p) => (
        <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
          {formatKPIValue(p.predicted_value, selectedKpi?.unit || 'currency', currency)}
        </span>
      ),
    },
    {
      key: 'range',
      header: '95% Confidence Band',
      align: 'right',
      render: (p) => {
        const low = p.range_low !== null ? p.range_low : p.predicted_value * 0.9;
        const high = p.range_high !== null ? p.range_high : p.predicted_value * 1.1;
        return (
          <span className="font-mono text-xs text-neutral-600 dark:text-neutral-300">
            {formatKPIValue(low, selectedKpi?.unit || 'currency', currency)} –{' '}
            {formatKPIValue(high, selectedKpi?.unit || 'currency', currency)}
          </span>
        );
      },
    },
    {
      key: 'confidence_level',
      header: 'Confidence',
      align: 'center',
      render: (p) => (
        <Badge
          variant={
            p.confidence_level === 'high'
              ? 'healthy'
              : p.confidence_level === 'moderate'
              ? 'warning'
              : 'critical'
          }
          size="xs"
          dot
        >
          {p.confidence_level.toUpperCase()}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={`${forecastHorizon}-Day Projection • ${confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence`}
        stageIcon={<LineChart className="w-4 h-4" />}
        title={`${forecastHorizon}-Day Predictions`}
        description="Forward statistical projections with 95% confidence variance bands calculated from your real business data."
        actions={
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <Button
              variant="outline"
              size="sm"
              isLoading={predLoading}
              onClick={() => fetchPredictions(forecastHorizon, selectedKpiId)}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${predLoading ? 'animate-spin' : ''}`} />}
            >
              Refresh Forecast
            </Button>
            <Badge variant="healthy" dot>
              {forecastHorizon}-Day Horizon
            </Badge>
          </div>
        }
      />

      {/* State View */}
      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchKpisAndData}
        loadingSkeleton="card-grid"
        isEmpty={kpis.length === 0}
        emptyIcon={LineChart}
        emptyTitle="No Business Data Uploaded for Forecasting"
        emptyDescription="Upload your business spreadsheet or report in the Data Pipeline to generate 7-day statistical predictions with confidence bands."
        emptyAction={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/data')}
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
          >
            Go to Data Pipeline to Upload File
          </Button>
        }
      >
        <div className="space-y-6">
          {/* KPI Selector Pills & Horizon Selector */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-[#15171C] p-4 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-xs">
            {/* KPI Metric Pills */}
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 md:pb-0">
              <span className="text-xs font-semibold text-neutral-500 font-mono">Select Metric:</span>
              {kpis.map((kpi) => (
                <button
                  key={kpi.id}
                  onClick={() => handleKpiSelect(kpi.id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl whitespace-nowrap transition-colors cursor-pointer ${
                    selectedKpiId === kpi.id
                      ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
                  }`}
                >
                  {kpi.name}
                </button>
              ))}
            </div>

            {/* Timeframe Horizon Toggle */}
            <div className="flex items-center space-x-1.5 shrink-0">
              <span className="text-xs font-semibold text-neutral-500 font-mono">Horizon:</span>
              {[7, 14, 30, 90].map((h) => (
                <button
                  key={h}
                  onClick={() => handleHorizonChange(h)}
                  className={`px-3 py-1 text-xs font-bold font-mono rounded-lg transition-colors cursor-pointer ${
                    forecastHorizon === h
                      ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
                  }`}
                >
                  {h}D
                </button>
              ))}
            </div>
          </div>

          {/* Forecast Chart with Shaded 95% Confidence Range Band */}
          {selectedKpi && (
            <PredictionRangeChart
              history={selectedKpi.recent_history || []}
              predictions={simulatedPredictions}
              kpiName={selectedKpi.name}
              unit={selectedKpi.unit}
              currency={currency}
              horizonDays={forecastHorizon}
            />
          )}

          {/* Interactive What-If Scenario Simulation Slider */}
          <Card className="p-5 sm:p-6 space-y-4 border-l-4 border-l-[#6B4226] dark:border-l-[#8C5E3C]">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
                <CardTitle>Interactive What-If Scenario Stress Testing</CardTitle>
              </div>
              <span className="font-mono text-sm font-bold text-[#6B4226] dark:text-[#8C5E3C]">
                {simulationMultiplier > 0 ? `+${simulationMultiplier}%` : `${simulationMultiplier}%`}
              </span>
            </div>

            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Adjust growth assumptions or market headwinds to recalculate forward forecast projections across the {forecastHorizon}-day horizon.
            </p>

            <div className="flex items-center space-x-4">
              <span className="text-xs font-mono text-neutral-400">-50%</span>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={simulationMultiplier}
                onChange={(e) => setSimulationMultiplier(parseInt(e.target.value, 10))}
                className="w-full h-2 bg-neutral-200 dark:bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#6B4226]"
              />
              <span className="text-xs font-mono text-neutral-400">+50%</span>
              <Button
                variant="outline"
                size="xs"
                onClick={() => setSimulationMultiplier(0)}
                disabled={simulationMultiplier === 0}
              >
                Reset
              </Button>
            </div>
          </Card>

          {/* Dense Table of Daily Projections */}
          <DenseTable
            columns={columns}
            data={simulatedPredictions}
            keyField="forecast_date"
            pageSize={10}
          />
        </div>
      </StateView>
    </div>
  );
};
