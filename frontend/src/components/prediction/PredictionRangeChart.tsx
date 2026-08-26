import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { LineChart, ShieldCheck, Calendar } from 'lucide-react';
import { Prediction } from '../../types/noah.types';
import { KPIValue } from '../../types/kpi.types';
import { formatKPIValue } from '../../utils/formatters';
import { useTheme } from '../../context/ThemeContext';
import { Badge } from '../ui/Badge';

interface PredictionRangeChartProps {
  history: KPIValue[];
  predictions: Prediction[];
  kpiName: string;
  unit: string;
  currency?: string;
  horizonDays?: number;
}

// Custom High-Precision Tooltip Component
const CustomPredictionTooltip: React.FC<{
  active?: boolean;
  payload?: any[];
  label?: string;
  unit: string;
  currency: string;
  kpiName: string;
}> = ({ active, payload, label, unit, currency, kpiName }) => {
  if (!active || !payload || payload.length === 0) return null;

  const dataPoint = payload[0]?.payload;
  if (!dataPoint) return null;

  const {
    displayDate,
    fullDate,
    historicalValue,
    forecastValue,
    rangeLow,
    rangeHigh,
    isForecast,
    isBridge,
  } = dataPoint;

  return (
    <div className="bg-white/95 dark:bg-[#15171C]/95 backdrop-blur-md border border-neutral-200 dark:border-neutral-700 rounded-xl p-3.5 shadow-xl text-xs space-y-2 min-w-[220px] max-w-[320px] pointer-events-none transition-all z-50">
      {/* Date Header */}
      <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-2">
        <div className="flex items-center space-x-1.5 text-neutral-600 dark:text-neutral-300 font-mono text-[11px] font-semibold">
          <Calendar className="w-3.5 h-3.5 text-neutral-400" />
          <span>{fullDate || displayDate || label}</span>
        </div>
        <span
          className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase ${
            isForecast && !isBridge
              ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
              : 'bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F]'
          }`}
        >
          {isForecast && !isBridge ? 'Projection' : isBridge ? 'Current State' : 'Observed'}
        </span>
      </div>

      {/* KPI Value Details */}
      <div className="space-y-1.5 pt-0.5">
        {historicalValue !== null && historicalValue !== undefined && (
          <div className="flex items-center justify-between gap-3">
            <span className="text-neutral-500 dark:text-neutral-400 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-[#6B4226] dark:bg-[#D5B79F] inline-block" />
              <span>Observed Value:</span>
            </span>
            <span className="font-mono font-bold text-neutral-900 dark:text-neutral-100">
              {formatKPIValue(historicalValue, unit, currency)}
            </span>
          </div>
        )}

        {forecastValue !== null && forecastValue !== undefined && (!isBridge || historicalValue === null) && (
          <div className="flex items-center justify-between gap-3">
            <span className="text-blue-600 dark:text-blue-400 flex items-center space-x-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
              <span>Projected Forecast:</span>
            </span>
            <span className="font-mono font-extrabold text-blue-600 dark:text-blue-400">
              {formatKPIValue(forecastValue, unit, currency)}
            </span>
          </div>
        )}

        {/* Confidence Variance Range for Future Points */}
        {isForecast && rangeLow !== null && rangeHigh !== null && rangeLow !== undefined && rangeHigh !== undefined && (
          <div className="pt-1.5 border-t border-neutral-100 dark:border-neutral-800/80 space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-neutral-500">95% Expected Range:</span>
              <span className="font-mono text-neutral-700 dark:text-neutral-300 font-semibold">
                {formatKPIValue(rangeLow, unit, currency)} – {formatKPIValue(rangeHigh, unit, currency)}
              </span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-neutral-400 font-mono">
              <span>Uncertainty Margin:</span>
              <span className="text-blue-600 dark:text-blue-400 font-semibold">
                ±{formatKPIValue(Math.max(0, (rangeHigh - rangeLow) / 2), unit, currency)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const PredictionRangeChart: React.FC<PredictionRangeChartProps> = ({
  history,
  predictions,
  kpiName,
  unit,
  currency = 'USD',
  horizonDays = 7,
}) => {
  const { isDark } = useTheme();

  // Combine history + forward predictions into a unified continuous series
  const chartData: any[] = [];

  // 1. Add historical actuals
  const historyLimit = horizonDays > 14 ? 30 : 14;
  const recentHistory = history.slice(-historyLimit);

  recentHistory.forEach((h) => {
    const d = new Date(h.timestamp);
    const isValidDate = !isNaN(d.getTime());
    const displayDate = isValidDate
      ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      : h.timestamp;
    const fullDate = isValidDate
      ? d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
      : h.timestamp;

    chartData.push({
      dateStr: h.timestamp.split('T')[0],
      displayDate,
      fullDate,
      historicalValue: h.value,
      forecastValue: null,
      rangeLow: null,
      rangeHigh: null,
      confidenceBand: null,
      isForecast: false,
      isBridge: false,
    });
  });

  // Connect last historical actual point seamlessly with the forecast curve
  if (recentHistory.length > 0 && predictions.length > 0) {
    const lastHist = recentHistory[recentHistory.length - 1];
    chartData[chartData.length - 1].forecastValue = lastHist.value;
    chartData[chartData.length - 1].rangeLow = lastHist.value;
    chartData[chartData.length - 1].rangeHigh = lastHist.value;
    chartData[chartData.length - 1].confidenceBand = [lastHist.value, lastHist.value];
    chartData[chartData.length - 1].isBridge = true;
  }

  // 2. Add forecast predictions with statistical upper and lower variance bounds
  predictions.forEach((p) => {
    const d = new Date(p.forecast_date);
    const isValidDate = !isNaN(d.getTime());
    const displayDate = isValidDate
      ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      : p.forecast_date;
    const fullDate = isValidDate
      ? d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
      : p.forecast_date;

    const low = p.range_low !== null && p.range_low !== undefined ? p.range_low : p.predicted_value * 0.9;
    const high = p.range_high !== null && p.range_high !== undefined ? p.range_high : p.predicted_value * 1.1;

    chartData.push({
      dateStr: p.forecast_date.split('T')[0],
      displayDate,
      fullDate,
      historicalValue: null,
      forecastValue: p.predicted_value,
      rangeLow: low,
      rangeHigh: high,
      confidenceBand: [low, high],
      isForecast: true,
      isBridge: false,
    });
  });

  const confidence = predictions.length > 0 ? predictions[0].confidence_level : 'moderate';
  const gridColor = isDark ? '#242831' : '#EAE4D9';
  const textColor = isDark ? '#A1A1AA' : '#71717A';

  return (
    <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 sm:p-6 space-y-5 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F]">
              <LineChart className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
              {kpiName} Statistical Forecast & Confidence Band
            </h3>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 font-normal">
            Observed history followed by a {horizonDays}-day forward trajectory with mathematically computed 95% variance bands.
          </p>
        </div>

        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <Badge
            variant={confidence === 'high' ? 'healthy' : confidence === 'moderate' ? 'warning' : 'critical'}
            size="sm"
            dot
          >
            Confidence: {confidence.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* Visual Guide Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#101216] border border-[#EBE4D8] dark:border-neutral-800">
        <div className="flex items-center space-x-2">
          <span className="w-4 h-0.5 bg-[#6B4226] dark:bg-[#D5B79F] inline-block rounded-full" />
          <span className="text-neutral-700 dark:text-neutral-300 font-semibold">Solid Line:</span>
          <span className="text-neutral-500">Observed History</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-blue-500 inline-block" />
          <span className="text-neutral-700 dark:text-neutral-300 font-semibold">Dashed Line:</span>
          <span className="text-neutral-500">Expected Forecast</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-3 bg-blue-500/25 dark:bg-blue-400/30 border border-blue-400/50 rounded-xs inline-block" />
          <span className="text-neutral-700 dark:text-neutral-300 font-semibold">Shaded Area:</span>
          <span className="text-neutral-500">95% Confidence Band</span>
        </div>
      </div>

      {/* Composed Chart with Native Range Shaded Confidence Interval */}
      <div className="h-80 sm:h-96 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 15, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="confidenceBandGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isDark ? '#3B82F6' : '#2563EB'} stopOpacity={0.38} />
                <stop offset="100%" stopColor={isDark ? '#3B82F6' : '#2563EB'} stopOpacity={0.10} />
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
              tickFormatter={(v) => formatKPIValue(v, unit, currency)}
              domain={['auto', 'auto']}
            />
            
            {/* Custom Interactive Tooltip */}
            <Tooltip
              content={
                <CustomPredictionTooltip
                  unit={unit}
                  currency={currency}
                  kpiName={kpiName}
                />
              }
              cursor={{ stroke: isDark ? '#4B5563' : '#D1D5DB', strokeWidth: 1, strokeDasharray: '4 4' }}
            />

            <Legend
              wrapperStyle={{ fontSize: '12px', paddingTop: '12px', color: textColor }}
              iconType="circle"
            />

            {/* Shaded Confidence Band (Range between RangeLow and RangeHigh) */}
            <Area
              type="monotone"
              dataKey="confidenceBand"
              name="95% Confidence Band"
              stroke={isDark ? '#60A5FA' : '#2563EB'}
              strokeWidth={1}
              strokeDasharray="3 3"
              fill="url(#confidenceBandGrad)"
              tooltipType="none"
              isAnimationActive={false}
            />

            {/* Upper Bound Line */}
            <Line
              type="monotone"
              dataKey="rangeHigh"
              name="Upper 95% Bound"
              stroke={isDark ? '#93C5FD' : '#60A5FA'}
              strokeWidth={1.2}
              strokeDasharray="2 2"
              dot={false}
              legendType="none"
              tooltipType="none"
              isAnimationActive={false}
            />

            {/* Lower Bound Line */}
            <Line
              type="monotone"
              dataKey="rangeLow"
              name="Lower 95% Bound"
              stroke={isDark ? '#93C5FD' : '#60A5FA'}
              strokeWidth={1.2}
              strokeDasharray="2 2"
              dot={false}
              legendType="none"
              tooltipType="none"
              isAnimationActive={false}
            />

            {/* Historical Solid Line */}
            <Line
              type="monotone"
              dataKey="historicalValue"
              name="Observed History"
              stroke={isDark ? '#D5B79F' : '#6B4226'}
              strokeWidth={2.5}
              dot={{ r: 3.5, fill: isDark ? '#D5B79F' : '#6B4226' }}
              activeDot={{ r: 6, stroke: isDark ? '#15171C' : '#FFFFFF', strokeWidth: 2 }}
            />

            {/* Forecast Dashed Line */}
            <Line
              type="monotone"
              dataKey="forecastValue"
              name="Projected Forecast"
              stroke={isDark ? '#60A5FA' : '#2563EB'}
              strokeWidth={2.5}
              strokeDasharray="5 5"
              dot={{ r: 4, fill: isDark ? '#60A5FA' : '#2563EB' }}
              activeDot={{ r: 6, stroke: isDark ? '#15171C' : '#FFFFFF', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="p-3 bg-neutral-50 dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 text-[11px] text-neutral-600 dark:text-neutral-400 flex flex-col sm:flex-row items-start sm:items-center justify-between font-mono gap-2">
        <span className="flex items-center space-x-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 inline shrink-0" />
          <span>Statistical Model: OLS Linear Trend Regression + 7-Day Cyclic Seasonality</span>
        </span>
        <span className="text-[#6B4226] dark:text-[#D5B79F] font-semibold">
          Prediction interval widens with future forecast distance
        </span>
      </div>
    </div>
  );
};
