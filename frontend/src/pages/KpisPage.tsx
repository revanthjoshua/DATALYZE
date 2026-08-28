import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Plus,
  ArrowUpRight,
  Download,
  Activity,
  Sparkles,
  BookOpen,
  Info,
  Layers,
  ArrowUpDown,
  Filter,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
} from 'lucide-react';
import { kpiApi } from '../api/kpiApi';
import { reportApi } from '../api/reportApi';
import { KPISummaryCard, KPIDefinition } from '../types/kpi.types';
import { formatKPIValue, formatPercentage } from '../utils/formatters';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { useDateRange } from '../context/DateRangeContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { PageHeader } from '../components/ui/PageHeader';
import { DenseTable, ColumnDef } from '../components/ui/DenseTable';
import { Modal } from '../components/ui/Modal';
import { FormField, Input, Select, Textarea } from '../components/ui/FormField';
import { StateView } from '../components/ui/StateView';

export const KpisPage: React.FC = () => {
  const { company } = useTenant();
  const toast = useToast();
  const navigate = useNavigate();
  const { timeRange } = useDateRange();

  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>(() => {
    return localStorage.getItem('datalyze_kpi_cat') || 'ALL';
  });
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('ALL');

  // Custom KPI Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [newKpiName, setNewKpiName] = useState('');
  const [newKpiCategory, setNewKpiCategory] = useState('Custom');
  const [newKpiUnit, setNewKpiUnit] = useState('currency');
  const [newKpiDirection, setNewKpiDirection] = useState<'increase_is_good' | 'decrease_is_good'>('increase_is_good');
  const [newKpiDescription, setNewKpiDescription] = useState('');

  // Definitions Modal State
  const [definitionModalKpi, setDefinitionModalKpi] = useState<KPISummaryCard | null>(null);

  // Form Validation Errors
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  const fetchKpis = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await kpiApi.getDashboardSummary();
      setKpis(data);
    } catch (err: any) {
      console.error('Failed to fetch KPIs', err);
      setErrorMsg('Failed to load metric baselines. Please verify backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKpis();
  }, []);

  const handleCategorySelect = (cat: string) => {
    setSelectedCategory(cat);
    localStorage.setItem('datalyze_kpi_cat', cat);
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!newKpiName.trim()) {
      errors.name = 'KPI metric name is required.';
    } else if (newKpiName.length < 3) {
      errors.name = 'Metric name must be at least 3 characters.';
    }

    if (!newKpiCategory.trim()) {
      errors.category = 'Category is required.';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateKpi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setModalLoading(true);

    try {
      const payload: Partial<KPIDefinition> = {
        name: newKpiName.trim(),
        key: newKpiName.trim().toLowerCase().replace(/[^a-z0-9]/g, '_'),
        category: newKpiCategory.trim(),
        unit: newKpiUnit,
        direction: newKpiDirection,
        description: newKpiDescription.trim() || undefined,
        calculation_cadence: 'daily',
        is_custom: true,
      };
      await kpiApi.createKPI(payload);
      toast.success(`Registered KPI model "${newKpiName}" to measurement pipeline.`, 'KPI Created');
      setIsModalOpen(false);
      setNewKpiName('');
      setNewKpiDescription('');
      setFormErrors({});
      await fetchKpis();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to create custom KPI formula.';
      setFormErrors({ general: msg });
      toast.error(msg, 'Creation Error');
    } finally {
      setModalLoading(false);
    }
  };

  const currency = company?.currency || 'USD';
  const categories = ['ALL', ...Array.from(new Set(kpis.map((k) => k.category)))];

  const filteredKpis = kpis.filter((kpi) => {
    const matchesCat = selectedCategory === 'ALL' || kpi.category === selectedCategory;
    const matchesStatus = selectedStatusFilter === 'ALL' || kpi.status.toUpperCase() === selectedStatusFilter;
    return matchesCat && matchesStatus;
  });

  const columns: ColumnDef<KPISummaryCard>[] = [
    {
      key: 'name',
      header: 'Metric Name',
      sortable: true,
      render: (kpi) => (
        <div className="font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-[#6B4226] dark:group-hover:text-[#8C5E3C] flex items-center space-x-1.5 font-sans">
          <span>{kpi.name}</span>
          <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-[#6B4226] dark:text-[#8C5E3C] transition-opacity" />
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      render: (kpi) => <Badge variant="brand">{kpi.category}</Badge>,
    },
    {
      key: 'current_value',
      header: 'Current Value',
      sortable: true,
      isNumeric: true,
      render: (kpi) => (
        <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100 font-mono">
          {formatKPIValue(kpi.current_value, kpi.unit, currency)}
        </span>
      ),
    },
    {
      key: 'percentage_change',
      header: 'Period Delta',
      sortable: true,
      isNumeric: true,
      render: (kpi) => {
        if (kpi.percentage_change !== null && kpi.percentage_change !== undefined) {
          const isGood =
            kpi.direction === 'increase_is_good'
              ? kpi.percentage_change >= 0
              : kpi.percentage_change <= 0;

          return (
            <span
              className={`font-semibold font-mono text-xs ${
                isGood ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
              }`}
            >
              {formatPercentage(kpi.percentage_change)}
            </span>
          );
        }
        return <span className="text-neutral-400 font-mono text-xs">Baseline pending</span>;
      },
    },
    {
      key: 'direction',
      header: 'Optimization Goal',
      render: (kpi) => (
        <span className="text-neutral-600 dark:text-neutral-400 font-sans text-xs">
          {kpi.direction === 'increase_is_good' ? 'Higher is better' : 'Lower is better'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center',
      sortable: true,
      render: (kpi) => {
        if (kpi.status === 'healthy') {
          return (
            <span className="badge-healthy px-2.5 py-1 text-xs inline-flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
              Healthy
            </span>
          );
        }
        if (kpi.status === 'warning') {
          return (
            <span className="badge-warning px-2.5 py-1 text-xs inline-flex items-center">
              <AlertTriangle className="w-3 h-3 mr-1" />
              Warning
            </span>
          );
        }
        if (kpi.status === 'critical') {
          return (
            <span className="badge-critical px-2.5 py-1 text-xs inline-flex items-center">
              <AlertCircle className="w-3 h-3 mr-1" />
              Critical
            </span>
          );
        }
        return <Badge variant="neutral">Active</Badge>;
      },
    },
    {
      key: 'definitions',
      header: 'Formula & Specs',
      align: 'center',
      render: (kpi) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setDefinitionModalKpi(kpi);
          }}
          className="text-[11px] text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 underline underline-offset-2 decoration-neutral-300 dark:decoration-neutral-700 flex items-center space-x-1 cursor-pointer mx-auto py-1 transition-colors"
          title="View formula definition and calculation specifications"
        >
          <BookOpen className="w-3 h-3 text-neutral-400" />
          <span>Definitions →</span>
        </button>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (kpi) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/kpis/${kpi.id}`);
          }}
          className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-bold text-white bg-[#6B4226] hover:bg-[#52321D] dark:bg-[#7A4B2C] dark:hover:bg-[#683E22] rounded-lg shadow-2xs font-mono uppercase tracking-wider transition-all cursor-pointer"
          title={`Drill down into ${kpi.name} metrics, segments, and baseline targets`}
        >
          <span>DRILL DOWN →</span>
        </button>
      ),
    },
  ];

  const totalMetrics = kpis.length;
  const criticalMetrics = kpis.filter((k) => (k.status || '').toLowerCase() === 'critical').length;

  const dynamicEyebrow =
    totalMetrics > 0
      ? `${totalMetrics} Monitored Metric${totalMetrics === 1 ? '' : 's'}${criticalMetrics > 0 ? ` • ${criticalMetrics} Needing Attention` : ' • 100% Healthy Baselines'}`
      : 'Metric Engine Ready • Awaiting Data';

  const [exportingCsv, setExportingCsv] = useState(false);

  const handleExportCsv = async () => {
    try {
      setExportingCsv(true);
      const blob = await reportApi.downloadKpiSummaryCsv();
      reportApi.triggerDownloadBlob(blob, 'datalyze_kpis_summary.csv');
      toast.success('KPI metrics exported to CSV successfully.', 'Export Complete');
    } catch (err: any) {
      toast.error('Failed to export KPI summary to CSV.', 'Export Error');
    } finally {
      setExportingCsv(false);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Top Page Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<Activity className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Key Performance Indicators & Formulas"
        description="Formulas, statistical baselines, and multi-dimensional performance tracking across business stages."
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportCsv}
              isLoading={exportingCsv}
              leftIcon={<Download className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />}
            >
              Export CSV
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              New Custom KPI
            </Button>
          </>
        }
      />

      {/* State Container for Table */}
      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchKpis}
        loadingSkeleton="table"
        isEmpty={kpis.length === 0}
        emptyIcon={TrendingUp}
        emptyTitle="No Business Metrics Available"
        emptyDescription="Upload your business spreadsheet or report in the Data Pipeline to start discovering and tracking your key metrics."
        emptyAction={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/data')}
            leftIcon={<TrendingUp className="w-3.5 h-3.5" />}
          >
            Go to Data Pipeline to Upload File
          </Button>
        }
      >
        {/* Category & Status Filter Pills */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-[#15171C] p-3 rounded-2xl border border-neutral-200 dark:border-neutral-800">
          {/* Category Pills */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
            <span className="text-xs font-semibold text-neutral-400 font-mono uppercase mr-1">Category:</span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => handleCategorySelect(cat)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg whitespace-nowrap transition-colors cursor-pointer ${
                  selectedCategory === cat
                    ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                    : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-neutral-100'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Status Filter Dropdown */}
          <div className="flex items-center space-x-2 shrink-0">
            <Filter className="w-3.5 h-3.5 text-neutral-400" />
            <select
              value={selectedStatusFilter}
              onChange={(e) => setSelectedStatusFilter(e.target.value)}
              className="px-2.5 py-1 rounded-xl text-xs bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200 focus:outline-none font-medium cursor-pointer"
            >
              <option value="ALL">All Statuses ({kpis.length})</option>
              <option value="HEALTHY">Healthy Only ({kpis.filter((k) => k.status === 'healthy').length})</option>
              <option value="WARNING">Warning Only ({kpis.filter((k) => k.status === 'warning').length})</option>
              <option value="CRITICAL">Critical Only ({kpis.filter((k) => k.status === 'critical').length})</option>
            </select>
          </div>
        </div>

        {/* Dense Table */}
        <DenseTable
          columns={columns}
          data={filteredKpis}
          keyField="id"
          onRowClick={(kpi) => navigate(`/kpis/${kpi.id}`)}
          searchPlaceholder="Search KPI metric name, category, or formula..."
          pageSize={10}
        />
      </StateView>

      {/* DEFINITIONS & FORMULA INSPECTION MODAL */}
      {definitionModalKpi && (
        <Modal
          isOpen={!!definitionModalKpi}
          onClose={() => setDefinitionModalKpi(null)}
          title={`KPI Specification: ${definitionModalKpi.name}`}
          description="Detailed calculation methodology, source columns, and statistical governance parameters."
          icon={<BookOpen className="w-5 h-5 text-[#6B4226]" />}
        >
          <div className="space-y-4 text-xs text-neutral-700 dark:text-neutral-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase font-mono">Metric Unit</span>
                <p className="font-semibold text-sm capitalize text-neutral-900 dark:text-neutral-100">
                  {definitionModalKpi.unit} ({company?.currency || 'USD'})
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase font-mono">Optimization Goal</span>
                <p className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
                  {definitionModalKpi.direction === 'increase_is_good' ? 'Higher is Better (Growth/Revenue)' : 'Lower is Better (Cost/Defect/Delay)'}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase font-mono">Aggregation Formula</span>
                <p className="font-mono text-xs text-neutral-900 dark:text-neutral-100 font-semibold">
                  {definitionModalKpi.unit === 'percentage' || definitionModalKpi.key.includes('rating') || definitionModalKpi.key.includes('time')
                    ? `MEAN( [${definitionModalKpi.key}] ) across time window`
                    : `SUM( [${definitionModalKpi.key}] ) across time window`}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 space-y-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase font-mono">Sampling Cadence</span>
                <p className="font-semibold text-xs text-neutral-900 dark:text-neutral-100">
                  {definitionModalKpi.calculation_cadence || 'Daily Continuous'} • {definitionModalKpi.recent_history?.length || 0} Recorded Points
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 space-y-1">
              <span className="text-[10px] font-bold text-neutral-400 uppercase font-mono">Business Purpose & Description</span>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed font-normal">
                {definitionModalKpi.description ||
                  `Direct quantitative telemetry extracted from uploaded column '${definitionModalKpi.key}'. Used to measure baseline variance, forecast future trajectory, and detect operational divergence.`}
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  const id = definitionModalKpi.id;
                  setDefinitionModalKpi(null);
                  navigate(`/kpis/${id}`);
                }}
              >
                Open Full Metric Drilldown →
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* CREATE CUSTOM KPI MODAL */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Register New Custom KPI Formula"
        description="Add a domain metric formula to your continuous measurement pipeline."
        icon={<Plus className="w-5 h-5 text-[#6B4226]" />}
      >
        <form onSubmit={handleCreateKpi} className="space-y-4">
          {formErrors.general && (
            <div className="p-3 text-xs bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-900">
              {formErrors.general}
            </div>
          )}

          <FormField
            label="Metric Display Name"
            error={formErrors.name}
            required
            helperText="e.g. Net Burn Rate, Unit Yield, Average Order Value"
          >
            <Input
              value={newKpiName}
              onChange={(e) => setNewKpiName(e.target.value)}
              placeholder="e.g. Gross Margin"
            />
          </FormField>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Category Group" error={formErrors.category} required>
              <Select
                value={newKpiCategory}
                onChange={(e) => setNewKpiCategory(e.target.value)}
              >
                <option value="Financial">Financial</option>
                <option value="Operations">Operations</option>
                <option value="Sales">Sales</option>
                <option value="Customer">Customer</option>
                <option value="Performance">Performance</option>
                <option value="Custom">Custom</option>
              </Select>
            </FormField>

            <FormField label="Unit Type" required>
              <Select
                value={newKpiUnit}
                onChange={(e) => setNewKpiUnit(e.target.value)}
              >
                <option value="currency">Currency ({currency})</option>
                <option value="percentage">Percentage (%)</option>
                <option value="number">Pure Number (Count)</option>
              </Select>
            </FormField>
          </div>

          <FormField label="Optimization Goal (Direction)" required>
            <Select
              value={newKpiDirection}
              onChange={(e) =>
                setNewKpiDirection(e.target.value as 'increase_is_good' | 'decrease_is_good')
              }
            >
              <option value="increase_is_good">Increase is Good (Revenue, Orders, Conversion)</option>
              <option value="decrease_is_good">Decrease is Good (Cost, Churn, Defect, Delay)</option>
            </Select>
          </FormField>

          <FormField label="Formula Description / Business Purpose">
            <Textarea
              value={newKpiDescription}
              onChange={(e) => setNewKpiDescription(e.target.value)}
              placeholder="Explain how this metric is computed and why it is critical for business operations..."
              rows={3}
            />
          </FormField>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={modalLoading}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Register Metric
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
