import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Database,
  Sparkles,
  ArrowRight,
  Activity,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  UploadCloud,
  FileSpreadsheet,
  ShieldAlert,
  Lightbulb,
  Boxes,
  Check,
  Zap,
  Table as TableIcon,
  Search,
  Eye,
} from 'lucide-react';

import { kpiApi } from '../api/kpiApi';
import { dataApi } from '../api/dataApi';
import { detectionApi } from '../api/detectionApi';
import { recommendationApi } from '../api/recommendationApi';
import { inventoryApi } from '../api/inventoryApi';

import { KPISummaryCard } from '../types/kpi.types';
import { DetectionEvent } from '../types/detection.types';
import { Recommendation } from '../types/noah.types';
import { InventoryDashboardSummary } from '../types/inventory.types';

import { KpiCard } from '../components/kpi/KpiCard';
import { KpiTrendChart } from '../components/kpi/KpiTrendChart';
import { DetectionCard } from '../components/detection/DetectionCard';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';

import { useAuth } from '../context/AuthContext';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { useDateRange } from '../context/DateRangeContext';

import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';
import { Drawer } from '../components/ui/Drawer';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { user } = useAuth();
  const { company } = useTenant();
  const toast = useToast();
  const { timeRange } = useDateRange();

  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [detections, setDetections] = useState<DetectionEvent[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [inventory, setInventory] =
    useState<InventoryDashboardSummary | null>(null);

  const [datasetInfo, setDatasetInfo] = useState<any>(null);
  const [datasetPreview, setDatasetPreview] = useState<any>(null);

  const [tableSearch, setTableSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [sampleLoading, setSampleLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [selectedKpiForChart, setSelectedKpiForChart] =
    useState<KPISummaryCard | null>(null);

  const [inspectedDetection, setInspectedDetection] =
    useState<DetectionEvent | null>(null);

  const [inspectedRecommendation, setInspectedRecommendation] =
    useState<Recommendation | null>(null);

  const [statusFilter, setStatusFilter] = useState<
    'ALL' | 'CRITICAL' | 'WARNING' | 'HEALTHY'
  >('ALL');

  const fetchAllDashboardData = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);

      const [kpiData, detData, recData, invData, infoData, prevData] =
        await Promise.all([
          kpiApi.getDashboardSummary(),
          detectionApi.getDetections(),
          recommendationApi.getRecommendations(),
          inventoryApi.getInventorySummary().catch(() => null),
          dataApi.getDatasetInfo().catch(() => null),
          dataApi.getDatasetPreview(10, 0).catch(() => null),
        ]);

      setKpis(kpiData);
      setDetections(detData);
      setRecommendations(recData);
      setInventory(invData);
      setDatasetInfo(infoData);
      setDatasetPreview(prevData);

      if (kpiData.length > 0 && !selectedKpiForChart) {
        setSelectedKpiForChart(kpiData[0]);
      }
    } catch (err: any) {
      console.error('Failed to fetch dashboard data', err);

      setErrorMsg(
        'Could not connect to the continuous intelligence backend. Please verify your connection.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllDashboardData();
  }, []);

  const handleLoadSample = async () => {
    try {
      setSampleLoading(true);

      toast.info(
        'Ingesting realistic 30-day company dataset...',
        'Data Pipeline'
      );

      await dataApi.loadSampleDataset();

      toast.success(
        'Sample dataset loaded! Running measurement & anomaly detection.',
        'Intelligence Engine'
      );

      await fetchAllDashboardData();
    } catch (err) {
      console.error('Failed to load sample dataset', err);

      toast.error(
        'Failed to load sample dataset. Please try again.',
        'Pipeline Error'
      );
    } finally {
      setSampleLoading(false);
    }
  };

  const handleAcknowledgeDetection = async (detId: number) => {
    try {
      await detectionApi.acknowledgeDetection(detId);

      setDetections((prev) =>
        prev.map((d) =>
          d.id === detId ? { ...d, status: 'acknowledged' } : d
        )
      );

      toast.success(
        'Anomaly divergence acknowledged and logged to audit trail.',
        'Triage Complete'
      );

      if (inspectedDetection?.id === detId) {
        setInspectedDetection(null);
      }
    } catch (err) {
      console.error('Failed to acknowledge detection', err);

      toast.error(
        'Could not update anomaly status. Please try again.',
        'Action Failed'
      );
    }
  };

  const handleStatusChange = async (
    recId: number,
    newStatus: 'open' | 'in_progress' | 'completed' | 'dismissed'
  ) => {
    try {
      await recommendationApi.updateStatus(recId, newStatus);

      setRecommendations((prev) =>
        prev.map((r) =>
          r.id === recId ? { ...r, status: newStatus } : r
        )
      );

      toast.success(
        `Action initiative updated to "${newStatus.replace('_', ' ')}".`,
        'Operational Prescriptions'
      );

      if (inspectedRecommendation?.id === recId) {
        setInspectedRecommendation((prev) =>
          prev ? { ...prev, status: newStatus } : null
        );
      }
    } catch (err) {
      console.error('Failed to update recommendation status', err);

      toast.error(
        'Failed to update recommendation status.',
        'Action Failed'
      );
    }
  };

  const hasData = kpis.some(
    (k) => k.current_value !== null && k.current_value !== undefined
  );

  const healthyCount = kpis.filter(
    (k) => k.status === 'healthy' && k.current_value !== null
  ).length;

  const warningCount = kpis.filter(
    (k) => k.status === 'warning' && k.current_value !== null
  ).length;

  const criticalCount = kpis.filter(
    (k) => k.status === 'critical' && k.current_value !== null
  ).length;

  const activeDetections = detections.filter(
    (d) => d.status === 'active'
  );

  const criticalDetections = activeDetections.filter(
    (d) => d.severity === 'critical'
  );

  const openRecommendations = recommendations.filter(
    (r) => r.status === 'open'
  );

  const criticalInventoryCount = (inventory?.items || []).filter(
    (i) => i.stockout_risk === 'critical'
  ).length;

  const totalNeedsAttention =
    criticalDetections.length +
    warningCount +
    openRecommendations.length +
    criticalInventoryCount;

  const activeDetectionsCount = (detections || []).filter(
    (d) => (d?.status || '').toLowerCase() === 'active'
  ).length;

  const dynamicEyebrow =
    activeDetectionsCount > 0
      ? `${activeDetectionsCount} Active Alert${
          activeDetectionsCount === 1 ? '' : 's'
        } • ${kpis.length} Monitored Numbers`
      : `${company?.name || 'Workspace'} • All Systems Healthy`;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        }
        title={`Welcome back, ${
          user?.full_name?.split(' ')[0] || 'Leader'
        }`}
        description={`Track your key numbers, catch sudden changes, and see 7-day predictions for ${
          company?.name || 'your business'
        }.`}
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchAllDashboardData}
              disabled={loading}
              title="Refresh All Numbers"
              leftIcon={
                <RefreshCw
                  className={`w-3.5 h-3.5 ${
                    loading ? 'animate-spin' : ''
                  }`}
                />
              }
            >
              Refresh
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/data')}
              leftIcon={
                <Database className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />
              }
            >
              Upload Data
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/reports')}
              leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
            >
              View Report
            </Button>
          </>
        }
      />

      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchAllDashboardData}
        loadingSkeleton="card-grid"
      >
        {!hasData ? (
          <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 sm:p-10 text-center space-y-6 shadow-xs relative overflow-hidden">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] flex items-center justify-center shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="max-w-xl mx-auto space-y-2">
              <h3 className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                No Business Data Uploaded Yet
              </h3>

              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed font-normal">
                Upload your company spreadsheet or operational data
                (Excel, CSV, Word table, or PDF) to automatically extract
                your metrics, anomaly alerts, 7-day predictions, and
                recommendations.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-left max-w-3xl mx-auto pt-2">
              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-[#6B4226] dark:text-[#D5B79F] font-mono block uppercase">
                  Step 1
                </span>

                <h4 className="font-semibold text-xs text-neutral-900 dark:text-neutral-100">
                  Upload Data File
                </h4>

                <p className="text-[11px] text-neutral-500">
                  Drop your Excel, CSV, Word, or PDF file into the Data
                  Pipeline.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-emerald-600 font-mono block uppercase">
                  Step 2
                </span>

                <h4 className="font-semibold text-xs text-neutral-900 dark:text-neutral-100">
                  Auto-Discovered KPIs & Alerts
                </h4>

                <p className="text-[11px] text-neutral-500">
                  Columns, trends, and unusual changes are detected
                  automatically from your file.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-blue-600 font-mono block uppercase">
                  Step 3
                </span>

                <h4 className="font-semibold text-xs text-neutral-900 dark:text-neutral-100">
                  Predictions & Action Steps
                </h4>

                <p className="text-[11px] text-neutral-500">
                  Receive statistical 7-day predictions and smart
                  operational recommendations.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={() => navigate('/data')}
                leftIcon={<FileSpreadsheet className="w-4 h-4" />}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Upload Business Data in Pipeline
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {datasetInfo && datasetInfo.has_dataset && (
              <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                <div className="flex items-center space-x-3 overflow-hidden">
                  <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-200 dark:border-emerald-900/50">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>

                  <div className="overflow-hidden">
                    <div className="flex items-center space-x-2 flex-wrap">
                      <span className="font-bold text-sm text-neutral-900 dark:text-neutral-100 font-mono truncate">
                        Connected Data File:{' '}
                        {datasetInfo.filename || 'Uploaded File'}
                      </span>

                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300">
                        CONNECTED
                      </span>
                    </div>

                    <p className="text-xs text-neutral-500 dark:text-neutral-400 font-mono mt-0.5">
                      {(
                        datasetInfo.total_rows ||
                        datasetInfo.row_count ||
                        0
                      ).toLocaleString()}{' '}
                      rows processed •{' '}
                      {datasetInfo.total_columns ||
                        datasetInfo.col_count ||
                        0}{' '}
                      columns • Currency: {company?.currency || 'INR'} •
                      Time Window: {timeRange}
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/data')}
                  leftIcon={
                    <Database className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />
                  }
                >
                  View & Upload Data
                </Button>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card
                onClick={() => setStatusFilter('ALL')}
                className={`p-5 flex flex-col justify-between cursor-pointer transition-all hover:shadow-md ${
                  statusFilter === 'ALL'
                    ? 'border-[#6B4226] ring-2 ring-[#6B4226] dark:border-[#8C5E3C] dark:ring-[#8C5E3C] bg-amber-50/10 dark:bg-amber-950/10'
                    : 'border-neutral-200 dark:border-neutral-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 font-mono">
                      All Metrics
                    </span>

                    <h4 className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-0.5">
                      Total Key Metrics
                    </h4>
                  </div>

                  <div className="p-2 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 shrink-0">
                    <Activity className="w-4 h-4" />
                  </div>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline space-x-2">
                    <p className="text-3xl font-extrabold text-neutral-900 dark:text-neutral-100 font-mono">
                      {kpis.length}
                    </p>

                    <span className="text-xs font-semibold text-neutral-500">
                      Tracked Metrics
                    </span>
                  </div>

                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                    All number columns from your uploaded file are tracked
                    live.
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-neutral-400 font-mono">
                    {statusFilter === 'ALL'
                      ? '● Showing all'
                      : 'Click to show all'}
                  </span>

                  <span className="text-[#6B4226] dark:text-[#8C5E3C] font-semibold">
                    View All →
                  </span>
                </div>
              </Card>

              <Card
                onClick={() =>
                  setStatusFilter(
                    statusFilter === 'HEALTHY' ? 'ALL' : 'HEALTHY'
                  )
                }
                className={`p-5 flex flex-col justify-between border-l-4 border-l-emerald-500 cursor-pointer transition-all hover:shadow-md ${
                  statusFilter === 'HEALTHY'
                    ? 'ring-2 ring-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20'
                    : 'border-neutral-200 dark:border-neutral-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 font-mono">
                      On Track
                    </span>

                    <h4 className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-0.5">
                      Healthy Metrics
                    </h4>
                  </div>

                  <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 shrink-0">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline space-x-2">
                    <p className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                      {healthyCount}
                    </p>

                    <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                      (
                      {kpis.length > 0
                        ? ((healthyCount / kpis.length) * 100).toFixed(0)
                        : 100}
                      % Healthy)
                    </span>
                  </div>

                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                    Numbers are tracking smoothly within normal daily
                    targets.
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-neutral-400 font-mono">
                    {statusFilter === 'HEALTHY'
                      ? '● Filter Active'
                      : 'Click to filter'}
                  </span>

                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                    Filter Healthy →
                  </span>
                </div>
              </Card>

              <Card
                onClick={() =>
                  setStatusFilter(
                    statusFilter === 'WARNING' ? 'ALL' : 'WARNING'
                  )
                }
                className={`p-5 flex flex-col justify-between border-l-4 border-l-amber-500 cursor-pointer transition-all hover:shadow-md ${
                  statusFilter === 'WARNING'
                    ? 'ring-2 ring-amber-500 bg-amber-50/20 dark:bg-amber-950/20'
                    : 'border-neutral-200 dark:border-neutral-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 font-mono">
                      Needs Attention
                    </span>

                    <h4 className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-0.5">
                      Warning Changes
                    </h4>
                  </div>

                  <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 shrink-0">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline space-x-2">
                    <p className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 font-mono">
                      {warningCount}
                    </p>

                    <span className="text-xs font-semibold text-amber-700 dark:text-amber-300">
                      Moderate Change
                    </span>
                  </div>

                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                    Metrics showing noticeable variations that may need
                    your attention.
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-neutral-400 font-mono">
                    {statusFilter === 'WARNING'
                      ? '● Filter Active'
                      : 'Click to filter'}
                  </span>

                  <span className="text-amber-600 dark:text-amber-400 font-semibold">
                    Filter Warnings →
                  </span>
                </div>
              </Card>

              <Card
                onClick={() =>
                  setStatusFilter(
                    statusFilter === 'CRITICAL' ? 'ALL' : 'CRITICAL'
                  )
                }
                className={`p-5 flex flex-col justify-between border-l-4 border-l-rose-500 cursor-pointer transition-all hover:shadow-md ${
                  statusFilter === 'CRITICAL'
                    ? 'ring-2 ring-rose-500 bg-rose-50/20 dark:bg-rose-950/20'
                    : 'border-neutral-200 dark:border-neutral-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 font-mono">
                      Urgent Action
                    </span>

                    <h4 className="text-xs font-bold text-neutral-900 dark:text-neutral-100 mt-0.5">
                      Critical Alerts
                    </h4>
                  </div>

                  <div className="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 shrink-0">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline space-x-2">
                    <p className="text-3xl font-extrabold text-rose-600 dark:text-rose-400 font-mono">
                      {criticalCount}
                    </p>

                    <span className="text-xs font-semibold text-rose-700 dark:text-rose-300">
                      Action Required
                    </span>
                  </div>

                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                    Significant drops or unusual changes that require
                    immediate action.
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-neutral-400 font-mono">
                    {statusFilter === 'CRITICAL'
                      ? '● Filter Active'
                      : 'Click to filter'}
                  </span>

                  <span className="text-rose-600 dark:text-rose-400 font-semibold">
                    Filter Critical →
                  </span>
                </div>
              </Card>
            </div>

            {statusFilter !== 'ALL' && (
              <div className="bg-[#FAF8F5] dark:bg-[#181A20] border border-neutral-300 dark:border-neutral-700 rounded-xl p-3 flex items-center justify-between shadow-2xs">
                <div className="flex items-center space-x-2 text-xs font-mono">
                  <span className="font-bold text-neutral-900 dark:text-neutral-100">
                    Active Filter: Showing {statusFilter} metrics
                  </span>

                  <span className="text-neutral-500">
                    (
                    {
                      kpis.filter(
                        (k) => k.status.toUpperCase() === statusFilter
                      ).length
                    }{' '}
                    of {kpis.length} shown)
                  </span>
                </div>

                <button
                  onClick={() => setStatusFilter('ALL')}
                  className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[#6B4226] text-white hover:bg-[#52321D] transition-colors cursor-pointer"
                >
                  Reset Filter (Show All) ✕
                </button>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <h3 className="text-xs font-bold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider font-mono">
                    Tracked Metric Baselines & Sparklines{' '}
                    {statusFilter !== 'ALL'
                      ? `(${statusFilter})`
                      : ''}
                  </h3>

                  {statusFilter !== 'ALL' && (
                    <Badge
                      variant={
                        statusFilter === 'CRITICAL'
                          ? 'critical'
                          : statusFilter === 'WARNING'
                          ? 'warning'
                          : 'healthy'
                      }
                      size="xs"
                    >
                      {
                        kpis.filter(
                          (k) => k.status.toUpperCase() === statusFilter
                        ).length
                      }{' '}
                      OF {kpis.length} SHOWN
                    </Badge>
                  )}
                </div>

                <button
                  onClick={() => navigate('/kpis')}
                  className="text-xs text-[#6B4226] dark:text-[#8C5E3C] hover:underline font-semibold flex items-center space-x-1 cursor-pointer"
                >
                  <span>View All Metrics Directory</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {kpis
                  .filter(
                    (k) =>
                      statusFilter === 'ALL' ||
                      k.status.toUpperCase() === statusFilter
                  )
                  .map((kpi) => (
                    <KpiCard
                      key={kpi.id || kpi.key}
                      kpi={kpi}
                    />
                  ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className="w-4 h-4 text-red-500" />

                    <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                      Active Baseline Divergences (
                      {activeDetections.length})
                    </h3>
                  </div>

                  <button
                    onClick={() => navigate('/alerts')}
                    className="text-xs text-[#6B4226] dark:text-[#8C5E3C] hover:underline font-semibold"
                  >
                    View all →
                  </button>
                </div>

                {activeDetections.length === 0 ? (
                  <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 text-center space-y-2 border-l-4 border-l-emerald-500">
                    <CheckCircle2 className="w-7 h-7 text-emerald-500 mx-auto" />

                    <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                      All Metrics Within Baseline Limits
                    </h4>

                    <p className="text-xs text-neutral-500">
                      Statistical z-score engine detected no significant
                      divergences in the last 7 days.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeDetections.slice(0, 3).map((det) => (
                      <div
                        key={det.id}
                        onClick={() => setInspectedDetection(det)}
                        className="cursor-pointer transition-transform hover:scale-[1.01]"
                      >
                        <DetectionCard
                          detection={det}
                          onAcknowledge={
                            handleAcknowledgeDetection
                          }
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="w-4 h-4 text-amber-500" />

                    <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                      Prescriptive Recommendations (
                      {openRecommendations.length})
                    </h3>
                  </div>

                  <button
                    onClick={() => navigate('/recommendations')}
                    className="text-xs text-[#6B4226] dark:text-[#8C5E3C] hover:underline font-semibold"
                  >
                    View all →
                  </button>
                </div>

                {openRecommendations.length === 0 ? (
                  <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 text-center space-y-2 border-l-4 border-l-emerald-500">
                    <CheckCircle2 className="w-7 h-7 text-emerald-500 mx-auto" />

                    <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                      No Action Items Pending
                    </h4>

                    <p className="text-xs text-neutral-500">
                      All recommended operational directives have been
                      reviewed or resolved.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {openRecommendations.slice(0, 3).map((rec) => (
                      <div
                        key={rec.id}
                        onClick={() =>
                          setInspectedRecommendation(rec)
                        }
                        className="cursor-pointer transition-transform hover:scale-[1.01]"
                      >
                        <RecommendationCard
                          recommendation={rec}
                          onStatusChange={handleStatusChange}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {datasetPreview &&
              datasetPreview.records &&
              datasetPreview.records.length > 0 && (
                <Card className="p-5 sm:p-6 space-y-4">
                  <CardHeader className="px-0 pt-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center space-x-2.5">
                      <div className="p-2 rounded-xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F]">
                        <TableIcon className="w-4 h-4" />
                      </div>

                      <div>
                        <div className="flex items-center space-x-2">
                          <CardTitle>
                            Uploaded File Records & Live Matrix
                          </CardTitle>

                          <Badge variant="healthy" size="xs">
                            {datasetPreview.total_rows ||
                              datasetPreview.records.length}{' '}
                            TOTAL ROWS
                          </Badge>
                        </div>

                        <p className="text-xs text-neutral-500 font-normal mt-0.5">
                          Direct cell inspection from{' '}
                          {datasetInfo?.filename ||
                            'uploaded document'}{' '}
                          • Showing first 10 rows
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />

                        <input
                          type="text"
                          value={tableSearch}
                          onChange={(e) =>
                            setTableSearch(e.target.value)
                          }
                          placeholder="Search records..."
                          className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-[#6B4226]"
                        />
                      </div>

                      <Button
                        variant="outline"
                        size="xs"
                        onClick={() => navigate('/data')}
                        leftIcon={
                          <Eye className="w-3 h-3 text-[#6B4226] dark:text-[#8C5E3C]" />
                        }
                      >
                        Open & Edit File →
                      </Button>

                      <Button
                        variant="outline"
                        size="xs"
                        onClick={() => navigate('/data')}
                        leftIcon={
                          <Database className="w-3 h-3 text-[#6B4226] dark:text-[#8C5E3C]" />
                        }
                      >
                        Query Sandbox →
                      </Button>
                    </div>
                  </CardHeader>

                  <div className="overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#15171C]">
                    <table className="w-full min-w-max text-xs text-left">
                      <thead className="bg-neutral-50 dark:bg-neutral-900/80 text-neutral-600 dark:text-neutral-300 font-semibold font-mono border-b border-neutral-200 dark:border-neutral-800">
                        <tr>
                          <th className="px-3.5 py-2.5 w-12 text-neutral-400">
                            #
                          </th>

                          {(datasetPreview.columns || []).map(
                            (col: string) => (
                              <th
                                key={col}
                                className="px-3.5 py-2.5 whitespace-nowrap min-w-[120px]"
                              >
                                {col
                                  .replace(/_/g, ' ')
                                  .toUpperCase()}
                              </th>
                            )
                          )}
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/80 font-mono">
                        {datasetPreview.records
                          .filter((r: any) =>
                            !tableSearch
                              ? true
                              : Object.values(r).some((v) =>
                                  String(v)
                                    .toLowerCase()
                                    .includes(
                                      tableSearch.toLowerCase()
                                    )
                                )
                          )
                          .map((row: any, idx: number) => (
                            <tr
                              key={idx}
                              className="hover:bg-neutral-50/80 dark:hover:bg-neutral-900/40 transition-colors"
                            >
                              <td className="px-3.5 py-2 text-neutral-400 text-[11px] font-bold">
                                {idx + 1}
                              </td>

                              {(datasetPreview.columns || []).map(
                                (col: string) => (
                                  <td
                                    key={col}
                                    className="px-3.5 py-2 text-neutral-800 dark:text-neutral-200 min-w-[120px]"
                                  >
                                    {row[col] !== null &&
                                    row[col] !== undefined
                                      ? String(row[col])
                                      : '—'}
                                  </td>
                                )
                              )}
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
          </div>
        )}
      </StateView>

      <Drawer
        isOpen={!!inspectedDetection}
        onClose={() => setInspectedDetection(null)}
        title={
          inspectedDetection
            ? `${
                inspectedDetection.kpi_name || 'Metric'
              } Baseline Divergence`
            : 'Anomaly Divergence Details'
        }
        subtitle={`Detected on ${
          inspectedDetection?.detected_at
            ? inspectedDetection.detected_at.split('T')[0]
            : 'recent timeline'
        }`}
        icon={<ShieldAlert className="w-5 h-5 text-red-500" />}
        footer={
          inspectedDetection && (
            <div className="flex items-center space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setInspectedDetection(null)}
              >
                Close
              </Button>

              {inspectedDetection.status === 'active' && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() =>
                    handleAcknowledgeDetection(
                      inspectedDetection.id
                    )
                  }
                  leftIcon={<Check className="w-3.5 h-3.5" />}
                >
                  Acknowledge & Dismiss
                </Button>
              )}
            </div>
          )
        }
      >
        {inspectedDetection && (
          <div className="space-y-5">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
              <span className="text-xs text-neutral-500 font-mono">
                Severity Rating:
              </span>

              <Badge
                variant={
                  inspectedDetection.severity === 'critical'
                    ? 'critical'
                    : inspectedDetection.severity === 'high'
                    ? 'warning'
                    : 'info'
                }
                dot
              >
                {inspectedDetection.severity}
              </Badge>
            </div>

            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase font-mono">
                Statistical Summary
              </h4>

              <p className="text-xs text-neutral-800 dark:text-neutral-200 leading-relaxed">
                Reading of {inspectedDetection.current_value}{' '}
                diverged by{' '}
                {inspectedDetection.percentage_change}% from
                baseline ({inspectedDetection.baseline_value}).
              </p>
            </div>

            {inspectedDetection.root_causes &&
              inspectedDetection.root_causes.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase font-mono">
                    Contributing Dimensional Factors
                  </h4>

                  <div className="space-y-1.5">
                    {inspectedDetection.root_causes.map((rc) => (
                      <div
                        key={rc.id}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 text-xs font-mono"
                      >
                        <div>
                          <span className="font-semibold text-neutral-800 dark:text-neutral-200 font-sans block">
                            {rc.explanation_text}
                          </span>

                          <span className="text-[10px] text-neutral-500 font-mono">
                            {rc.dimension_name}:{' '}
                            {rc.dimension_value}
                          </span>
                        </div>

                        <span className="text-amber-600 dark:text-amber-400 font-bold shrink-0">
                          {rc.contribution_percentage.toFixed(0)}%
                          contribution
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </div>
        )}
      </Drawer>

      <Drawer
        isOpen={!!inspectedRecommendation}
        onClose={() => setInspectedRecommendation(null)}
        title={
          inspectedRecommendation?.title ||
          'Prescriptive Initiative Details'
        }
        subtitle={`Priority: ${
          inspectedRecommendation?.priority.toUpperCase()
        } • Impact: ${
          inspectedRecommendation?.impact_level?.toUpperCase() ||
          'HIGH'
        }`}
        icon={<Lightbulb className="w-5 h-5 text-amber-500" />}
        footer={
          inspectedRecommendation && (
            <div className="flex items-center space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  setInspectedRecommendation(null)
                }
              >
                Close
              </Button>

              {inspectedRecommendation.status !== 'completed' && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() =>
                    handleStatusChange(
                      inspectedRecommendation.id,
                      'completed'
                    )
                  }
                  leftIcon={<Check className="w-3.5 h-3.5" />}
                >
                  Mark as Resolved
                </Button>
              )}
            </div>
          )
        }
      >
        {inspectedRecommendation && (
          <div className="space-y-5">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
              <span className="text-xs text-neutral-500 font-mono">
                Current Status:
              </span>

              <Badge
                variant={
                  inspectedRecommendation.status === 'completed'
                    ? 'healthy'
                    : inspectedRecommendation.status ===
                      'in_progress'
                    ? 'info'
                    : 'warning'
                }
              >
                {inspectedRecommendation.status.replace('_', ' ')}
              </Badge>
            </div>

            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase font-mono">
                Operational Action Directive
              </h4>

              <p className="text-xs text-neutral-800 dark:text-neutral-200 leading-relaxed font-semibold">
                {inspectedRecommendation.action_text}
              </p>

              {inspectedRecommendation.rationale && (
                <p className="text-xs text-neutral-500 pt-1 leading-relaxed">
                  Rationale:{' '}
                  {inspectedRecommendation.rationale}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                  Category
                </span>

                <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200 mt-1 block">
                  {inspectedRecommendation.category}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                  Estimated Impact
                </span>

                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 mt-1 block uppercase">
                  {inspectedRecommendation.impact_level} Impact
                </span>
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};