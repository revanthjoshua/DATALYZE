import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowUpRight,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, YAxis } from 'recharts';
import { KPISummaryCard } from '../../types/kpi.types';
import { formatKPIValue, formatPercentage } from '../../utils/formatters';
import { useTenant } from '../../context/TenantContext';
import { useTheme } from '../../context/ThemeContext';

interface KpiCardProps {
  kpi: KPISummaryCard;
  onAskNoah?: (kpiName: string) => void;
}

export const KpiCard: React.FC<KpiCardProps> = ({ kpi, onAskNoah }) => {
  const navigate = useNavigate();
  const { company } = useTenant();
  const { isDark } = useTheme();
  const currency = company?.currency || 'USD';

  const isUp = kpi.trend_direction === 'up';
  const isDown = kpi.trend_direction === 'down';

  // Format sparkline chart data
  const chartData = (kpi.recent_history || []).map((h) => ({
    date: h.timestamp ? h.timestamp.split('T')[0] : 'recent',
    value: h.value ?? 0,
  }));

  const isGoodChange =
    (kpi.direction === 'increase_is_good' && (kpi.percentage_change || 0) >= 0) ||
    (kpi.direction === 'decrease_is_good' && (kpi.percentage_change || 0) <= 0);

  const sparklineColor = isGoodChange
    ? (isDark ? '#4ADE80' : '#16A34A')
    : (isDark ? '#F87171' : '#DC2626');

  const isAvg =
    kpi.unit === 'percentage' ||
    kpi.key.toLowerCase().includes('rating') ||
    kpi.key.toLowerCase().includes('time') ||
    kpi.key.toLowerCase().includes('rate');

  const handleCardClick = () => {
    navigate(`/kpis/${kpi.id || kpi.key}`);
  };

  const statusBorderColor =
    kpi.status === 'critical'
      ? 'border-red-300 dark:border-red-900/60 shadow-red-500/5'
      : kpi.status === 'warning'
      ? 'border-amber-300 dark:border-amber-900/60 shadow-amber-500/5'
      : 'border-neutral-200/80 dark:border-neutral-800';

  return (
    <div
      onClick={handleCardClick}
      className={`group relative glass-card glass-card-hover p-5 sm:p-6 cursor-pointer flex flex-col justify-between h-full space-y-4 hover:shadow-lg transition-all duration-200 border ${statusBorderColor}`}
    >
      {/* Top row: Category tag, Full Column Title & Status Badge */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-bold tracking-wider text-neutral-600 dark:text-neutral-300 uppercase font-mono bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded border border-neutral-200 dark:border-neutral-700">
            {kpi.category || 'Business Metric'}
          </span>

          <div className="flex items-center space-x-1.5 shrink-0">
            {kpi.status === 'healthy' && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold font-mono bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
                HEALTHY
              </span>
            )}
            {kpi.status === 'warning' && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold font-mono bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />
                WARNING
              </span>
            )}
            {kpi.status === 'critical' && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold font-mono bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 animate-pulse">
                <AlertCircle className="w-3 h-3 mr-1 text-red-600" />
                CRITICAL
              </span>
            )}
            <div className="p-1 rounded-md text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-200 group-hover:bg-neutral-100 dark:group-hover:bg-neutral-800 transition-colors">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Full un-truncated column name from uploaded file */}
        <div>
          <h3
            title={kpi.name}
            className="font-bold text-neutral-900 dark:text-neutral-100 text-base sm:text-lg leading-snug break-words group-hover:text-[#6B4226] dark:group-hover:text-[#D5B79F] transition-colors"
          >
            {kpi.name}
          </h3>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400 font-sans mt-0.5">
            {isAvg ? 'Sample Average' : 'Aggregate Volume'} • {chartData.length} records parsed
          </p>
        </div>
      </div>

      {/* Middle row: Large Metric Value, Baseline context & Sparkline */}
      <div className="flex items-end justify-between gap-3 pt-1">
        <div className="space-y-1.5">
          <p className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-50 font-mono">
            {formatKPIValue(kpi.current_value, kpi.unit, currency)}
          </p>

          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            {kpi.percentage_change !== null && kpi.percentage_change !== undefined ? (
              <div
                className={`flex items-center text-xs font-bold font-mono px-2 py-0.5 rounded-md ${
                  isGoodChange
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                    : 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                }`}
              >
                {isUp && <TrendingUp className="w-3.5 h-3.5 mr-1" />}
                {isDown && <TrendingDown className="w-3.5 h-3.5 mr-1" />}
                {!isUp && !isDown && <Minus className="w-3.5 h-3.5 mr-1" />}
                <span>{formatPercentage(kpi.percentage_change)} vs baseline</span>
              </div>
            ) : (
              <span className="text-xs text-neutral-400 font-mono">
                {chartData.length > 0 ? `${chartData.length} data points` : 'Baseline pending'}
              </span>
            )}
          </div>

          {/* Explicit previous value baseline comparison */}
          {kpi.previous_value !== undefined && kpi.previous_value !== null && (
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400 font-mono">
              Baseline: <span className="font-semibold text-neutral-700 dark:text-neutral-300">{formatKPIValue(kpi.previous_value, kpi.unit, currency)}</span>
            </p>
          )}
        </div>

        {/* Sparkline visualization */}
        {chartData.length > 1 && (
          <div className="w-24 sm:w-28 h-12 shrink-0 pb-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id={`grad-${kpi.id || kpi.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={sparklineColor} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={sparklineColor} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <YAxis domain={['auto', 'auto']} hide />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={sparklineColor}
                  strokeWidth={2.2}
                  fillOpacity={1}
                  fill={`url(#grad-${kpi.id || kpi.key})`}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Target Direction and Interactive Drill Down Button */}
      <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
        <span className="font-sans">
          Target:{' '}
          <strong className="text-neutral-800 dark:text-neutral-200 font-semibold">
            {kpi.direction === 'increase_is_good' ? 'Higher is better' : 'Lower is better'}
          </strong>
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/kpis/${kpi.id || kpi.key}`);
          }}
          className="text-[#6B4226] dark:text-[#D5B79F] hover:text-white dark:hover:text-white hover:bg-[#6B4226] dark:hover:bg-[#8C5E3C] font-mono text-[11px] uppercase font-bold flex items-center space-x-1 cursor-pointer bg-neutral-100 dark:bg-neutral-800 px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 transition-all shadow-2xs"
          title={`Drill down to inspect ${kpi.name} historical telemetry, dimensions, and targets`}
        >
          <span>DRILL DOWN</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
