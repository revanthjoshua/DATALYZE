import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Layers,
  Sparkles,
  TrendingUp,
  Target,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Activity,
  ArrowUpRight,
} from 'lucide-react';
import { kpiApi } from '../api/kpiApi';
import { KPISummaryCard } from '../types/kpi.types';
import { KpiTrendChart } from '../components/kpi/KpiTrendChart';
import { useTenant } from '../context/TenantContext';
import { useDateRange } from '../context/DateRangeContext';
import { formatKPIValue, formatPercentage } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';
import { DenseTable, ColumnDef } from '../components/ui/DenseTable';

interface DimensionSlice {
  dimension_value: string;
  total_value: number;
  percentage_contribution: number;
}

export const KpiDetailPage: React.FC = () => {
  const params = useParams<{ kpiId?: string; id?: string }>();
  const navigate = useNavigate();
  const { company } = useTenant();
  const { timeRange } = useDateRange();

  const rawParam = (params.kpiId || params.id || '').trim();
  const kpiId = parseInt(rawParam, 10);

  const [kpi, setKpi] = useState<KPISummaryCard | null>(null);
  const [selectedDim, setSelectedDim] = useState<string>('region');
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      setKpi(null);
      const allKpis = await kpiApi.getDashboardSummary(timeRange);

      const normalizedParam = rawParam.toLowerCase();
      let current =
        allKpis.find(
          (k) => String(k.id) === rawParam || (!isNaN(kpiId) && k.id === kpiId)
        ) || null;

      if (!current) {
        current =
          allKpis.find(
            (k) =>
              (k.key || '').toLowerCase() === normalizedParam ||
              (k.name || '').toLowerCase() === normalizedParam ||
              (k.name || '').toLowerCase().replace(/\s+/g, '_') === normalizedParam ||
              (k.name || '').toLowerCase().replace(/\s+/g, '-') === normalizedParam
          ) || null;
      }

      if (!current) {
        setErrorMsg(`Metric details not found in active workspace.`);
      } else {
        setKpi(current);
      }
    } catch (err) {
      console.error('Failed to fetch KPI detail', err);
      setErrorMsg('Failed to load metric details from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [rawParam, timeRange]);

  const currency = company?.currency || 'USD';

  // Discover all dimensions recorded in history
  const availableDimensions = React.useMemo(() => {
    if (!kpi || !kpi.recent_history) return [];
    const dims = new Set<string>();
    kpi.recent_history.forEach((h) => {
      if (h.dimension_data && typeof h.dimension_data === 'object') {
        Object.keys(h.dimension_data).forEach((k) => {
          if (!k.startsWith('_')) {
            dims.add(k);
          }
        });
      }
    });
    return Array.from(dims);
  }, [kpi]);

  useEffect(() => {
    if (availableDimensions.length > 0 && !availableDimensions.includes(selectedDim)) {
      setSelectedDim(availableDimensions[0]);
    }
  }, [availableDimensions]);

  // Compute dimension breakdown from recent history safely
  const breakdown: DimensionSlice[] = React.useMemo(() => {
    if (!kpi || !kpi.recent_history || kpi.recent_history.length === 0) return [];

    const segmentTotals: Record<string, number> = {};
    let grandTotal = 0;

    kpi.recent_history.forEach((h) => {
      if (!h.dimension_data || typeof h.dimension_data !== 'object') return;
      const rawDim = h.dimension_data[selectedDim];

      if (typeof rawDim === 'object' && rawDim !== null) {
        // If nested map { "North": 50, "South": 30 }
        Object.entries(rawDim).forEach(([k, v]) => {
          const num = typeof v === 'number' ? v : parseFloat(String(v)) || 0;
          segmentTotals[k] = (segmentTotals[k] || 0) + num;
          grandTotal += num;
        });
      } else if (rawDim !== undefined && rawDim !== null && !String(rawDim).startsWith('_')) {
        // If flat row {"region": "North"}
        const segName = String(rawDim);
        const val = typeof h.value === 'number' ? h.value : parseFloat(String(h.value)) || 0;
        segmentTotals[segName] = (segmentTotals[segName] || 0) + val;
        grandTotal += val;
      }
    });

    const entries = Object.entries(segmentTotals);
    if (entries.length === 0) return [];

    return entries
      .map(([key, val]) => ({
        dimension_value: key,
        total_value: typeof val === 'number' ? val : 0,
        percentage_contribution: grandTotal > 0 ? ((val / grandTotal) * 100) : 0,
      }))
      .sort((a, b) => b.total_value - a.total_value);
  }, [kpi, selectedDim]);

  const dimColumns: ColumnDef<DimensionSlice>[] = [
    {
      key: 'dimension_value',
      header: 'Segment / Slice Value',
      sortable: true,
      render: (row) => (
        <span className="font-semibold text-neutral-900 dark:text-neutral-100 font-sans">
          {row.dimension_value}
        </span>
      ),
    },
    {
      key: 'total_value',
      header: 'Contribution Value',
      sortable: true,
      isNumeric: true,
      render: (row) => (
        <span className="font-bold text-neutral-900 dark:text-neutral-100 font-mono">
          {formatKPIValue(row.total_value ?? 0, kpi?.unit || 'currency', currency)}
        </span>
      ),
    },
    {
      key: 'percentage_contribution',
      header: '% Total Share',
      sortable: true,
      isNumeric: true,
      render: (row) => {
        const pct = typeof row.percentage_contribution === 'number' ? row.percentage_contribution : 0;
        return (
          <div className="flex items-center justify-end space-x-2">
            <span className="font-semibold font-mono text-[#6B4226] dark:text-[#8C5E3C]">
              {pct.toFixed(1)}%
            </span>
            <div className="w-16 h-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
              <div
                className="h-full bg-[#6B4226] dark:bg-[#8C5E3C] rounded-full"
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
          </div>
        );
      },
    },
  ];

  const dynamicEyebrow = kpi
    ? `${kpi.category || 'Business Metric'} • ${kpi.percentage_change == null ? 'NO COMPARISON' : kpi.status.toUpperCase()} (${kpi.direction === 'increase_is_good' ? 'Higher is better' : 'Lower is better'})`
    : 'Metric Detail Drilldown';

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Page Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<TrendingUp className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title={kpi?.name || 'KPI Metric Deep Dive'}
        description={kpi?.description || 'Recorded observations and dimension breakdowns for the selected period'}
        actions={
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/kpis')}
              leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
            >
              All Metrics Directory
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/')}
            >
              Dashboard
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/analysis')}
              leftIcon={<Target className="w-3.5 h-3.5" />}
            >
              Analysis Objectives
            </Button>
          </div>
        }
      />

      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchDetail}
        loadingSkeleton="chart"
      >
        {kpi && (
          <div className="space-y-6 sm:space-y-8">
            {/* KPI Executive Summary Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-5 flex flex-col justify-between border-l-4 border-l-[#6B4226]">
                <div>
                  <span className="text-[10px] font-bold text-neutral-500 font-mono block uppercase">
                    Current Reading
                  </span>
                  <p className="text-2xl sm:text-3xl font-extrabold text-neutral-900 dark:text-neutral-100 font-mono mt-1">
                    {formatKPIValue(kpi.current_value, kpi.unit, currency)}
                  </p>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <Badge variant="brand">{kpi.category || 'Metric'}</Badge>
                  <span className="text-[11px] text-neutral-400 font-mono">
                    {kpi.recent_history?.length || 0} samples
                  </span>
                </div>
              </Card>

              <Card className="p-5 flex flex-col justify-between border-l-4 border-l-blue-500">
                <div>
                  <span className="text-[10px] font-bold text-neutral-500 font-mono block uppercase">
                    Change vs Previous Observation
                  </span>
                  <p className="text-2xl sm:text-3xl font-extrabold font-mono mt-1">
                    {kpi.percentage_change !== null && kpi.percentage_change !== undefined ? (
                      <span
                        className={
                          (kpi.direction === 'increase_is_good' && kpi.percentage_change >= 0) ||
                          (kpi.direction === 'decrease_is_good' && kpi.percentage_change <= 0)
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }
                      >
                        {formatPercentage(kpi.percentage_change)}
                      </span>
                    ) : (
                      '—'
                    )}
                  </p>
                </div>
                <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-2 font-sans">
                  {kpi.previous_value !== undefined && kpi.previous_value !== null
                    ? `Previous: ${formatKPIValue(kpi.previous_value, kpi.unit, currency)}`
                    : 'No comparable previous observation'}
                </p>
              </Card>

              <Card className="p-5 flex flex-col justify-between border-l-4 border-l-amber-500">
                <div>
                  <span className="text-[10px] font-bold text-neutral-500 font-mono block uppercase">
                    Change Indicator
                  </span>
                  <div className="mt-2">
                    {kpi.percentage_change == null ? <span className="text-sm text-neutral-500">No comparison available</span> : kpi.status === 'healthy' && (
                      <span className="badge-healthy px-2.5 py-1 text-xs inline-flex items-center">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                        FAVORABLE CHANGE
                      </span>
                    )}
                    {kpi.status === 'warning' && (
                      <span className="badge-warning px-2.5 py-1 text-xs inline-flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
                        ADVERSE CHANGE
                      </span>
                    )}
                    {kpi.status === 'critical' && (
                      <span className="badge-critical px-2.5 py-1 text-xs inline-flex items-center animate-pulse">
                        <AlertCircle className="w-3.5 h-3.5 mr-1 text-red-600" />
                        LARGE ADVERSE CHANGE
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-[11px] text-neutral-400 mt-2 font-sans">
                  Based on the last two dated observations and metric direction; adverse changes over 7% are flagged.
                </p>
              </Card>

              <Card className="p-5 flex flex-col justify-between border-l-4 border-l-emerald-500">
                <div>
                  <span className="text-[10px] font-bold text-neutral-500 font-mono block uppercase">
                    Data Updates
                  </span>
                  <p className="text-2xl sm:text-3xl font-extrabold text-[#6B4226] dark:text-[#8C5E3C] font-mono mt-1">
                    On Import
                  </p>
                </div>
                <p className="text-[11px] text-neutral-400 mt-2 font-sans">
                  Recomputed when your dataset changes
                </p>
              </Card>
            </div>

            {/* Historical Trend Chart */}
            <KpiTrendChart
              values={kpi.recent_history || []}
              unit={kpi.unit || 'currency'}
              currency={currency}
              name={kpi.name}
            />

            {/* Dimensional Slice Breakdown Table */}
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                    Dimensional Contribution Slices
                  </h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-xs text-neutral-500 font-mono">Dimension:</span>
                  <div className="flex items-center space-x-1">
                    {availableDimensions.map((dim) => (
                      <button
                        key={dim}
                        onClick={() => setSelectedDim(dim)}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-lg uppercase tracking-wider transition-colors cursor-pointer ${
                          selectedDim === dim
                            ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                            : 'bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
                        }`}
                      >
                        {dim}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {breakdown.length === 0 ? (
                <Card className="p-8 text-center text-xs text-neutral-500">
                  No recorded values are available for this dimension.
                </Card>
              ) : (
                <DenseTable
                  columns={dimColumns}
                  data={breakdown}
                  keyField="dimension_value"
                  searchable={false}
                  pageSize={10}
                />
              )}
            </div>
          </div>
        )}
      </StateView>

    </div>
  );
};
