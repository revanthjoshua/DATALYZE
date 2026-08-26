import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Activity } from 'lucide-react';
import { KPIValue } from '../../types/kpi.types';
import { formatKPIValue } from '../../utils/formatters';
import { useTheme } from '../../context/ThemeContext';

interface KpiTrendChartProps {
  values: KPIValue[];
  unit: string;
  currency?: string;
  name: string;
}

export const KpiTrendChart: React.FC<KpiTrendChartProps> = ({
  values,
  unit,
  currency = 'USD',
  name,
}) => {
  const { isDark } = useTheme();
  const [timeRange, setTimeRange] = useState<'7D' | '14D' | '30D' | 'ALL'>('30D');

  let filteredValues = [...values];
  if (timeRange === '7D') filteredValues = filteredValues.slice(-7);
  else if (timeRange === '14D') filteredValues = filteredValues.slice(-14);
  else if (timeRange === '30D') filteredValues = filteredValues.slice(-30);

  const chartData = filteredValues.map((v, idx) => {
    let label = (v.dimension_data as any)?._row_label;
    if (!label) {
      try {
        label = new Date(v.timestamp).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
        });
      } catch {
        label = `Row ${idx + 1}`;
      }
    }
    return {
      date: v.timestamp.split('T')[0],
      displayDate: label,
      value: v.value,
    };
  });

  const numericVals = chartData.map((d) => d.value);
  const maxVal = numericVals.length > 0 ? Math.max(...numericVals) : 0;
  const minVal = numericVals.length > 0 ? Math.min(...numericVals) : 0;
  const avgVal =
    numericVals.length > 0 ? numericVals.reduce((a, b) => a + b, 0) / numericVals.length : 0;

  const gridColor = isDark ? '#242831' : '#E5DFD4';
  const textColor = isDark ? '#A1A1AA' : '#71717A';

  return (
    <div className="glass-panel p-5 sm:p-6 space-y-5">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-brand-700 dark:text-brand-400" />
            <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
              {name} Historical Trend
            </h3>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 font-medium">
            Automated continuous daily measurements & baseline trajectory
          </p>
        </div>

        {/* Time Range Selector Tabs */}
        <div className="flex items-center space-x-1 bg-neutral-100 dark:bg-neutral-900 p-1 rounded-lg border border-neutral-200 dark:border-neutral-800 self-start sm:self-auto">
          {(['7D', '14D', '30D', 'ALL'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                timeRange === r
                  ? 'bg-brand-700 text-white shadow-xs'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Mini Stats Ribbon */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-3 gap-3 p-3 bg-neutral-50 dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 text-xs font-mono">
          <div>
            <span className="text-[10px] text-neutral-500 uppercase block font-sans font-semibold">Period Mean</span>
            <span className="font-bold text-neutral-900 dark:text-neutral-100 text-sm">{formatKPIValue(avgVal, unit, currency)}</span>
          </div>
          <div>
            <span className="text-[10px] text-status-healthy-text uppercase block font-sans font-semibold">Period Peak</span>
            <span className="font-bold text-status-healthy-text text-sm">{formatKPIValue(maxVal, unit, currency)}</span>
          </div>
          <div>
            <span className="text-[10px] text-status-critical-text uppercase block font-sans font-semibold">Period Trough</span>
            <span className="font-bold text-status-critical-text text-sm">{formatKPIValue(minVal, unit, currency)}</span>
          </div>
        </div>
      )}

      {/* Recharts Area Chart */}
      <div className="h-72 sm:h-80 w-full pt-2">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-neutral-400 text-sm font-medium">
            No historical time-series data available. Ingest data via Data Pipeline.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="kpiMainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={isDark ? '#8C5E3C' : '#6B4226'} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={isDark ? '#8C5E3C' : '#6B4226'} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis
                dataKey="displayDate"
                stroke={textColor}
                tick={{ fontSize: 11, fill: textColor, fontWeight: 500 }}
                tickLine={false}
                axisLine={{ stroke: gridColor }}
              />
              <YAxis
                stroke={textColor}
                tick={{ fontSize: 11, fill: textColor, fontWeight: 500 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => formatKPIValue(val, unit, currency)}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#181A20' : '#FFFFFF',
                  borderColor: isDark ? '#272B35' : '#E5DFD4',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: isDark ? '#F3F4F6' : '#18181B',
                  boxShadow: '0 8px 24px -6px rgba(0, 0, 0, 0.15)',
                  fontWeight: 500,
                }}
                formatter={(val: any) => [formatKPIValue(val, unit, currency), name]}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={isDark ? '#D5B79F' : '#6B4226'}
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#kpiMainGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
