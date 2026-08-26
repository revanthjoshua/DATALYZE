import React, { useState } from 'react';
import {
  TrendingDown,
  TrendingUp,
  Layers,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  HelpCircle,
} from 'lucide-react';
import { DetectionEvent } from '../../types/detection.types';
import { formatPercentage, formatRelativeTime } from '../../utils/formatters';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface DetectionCardProps {
  detection: DetectionEvent;
  onAcknowledge?: (id: number) => void;
  onAskNoah?: (prompt: string) => void;
}

export const DetectionCard: React.FC<DetectionCardProps> = ({
  detection,
  onAcknowledge,
  onAskNoah,
}) => {
  const [expanded, setExpanded] = useState<boolean>(true);

  const isDown = detection.direction === 'down';
  const severityBorder = {
    critical: 'border-l-4 border-l-red-500',
    high: 'border-l-4 border-l-amber-500',
    medium: 'border-l-4 border-l-[#6B4226] dark:border-l-[#8C5E3C]',
    low: 'border-l-4 border-l-neutral-400',
  }[detection.severity] || 'border-l-4 border-l-amber-500';

  return (
    <div
      className={`bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 sm:p-6 transition-all duration-150 shadow-xs hover:border-neutral-300 dark:hover:border-neutral-700 ${severityBorder}`}
    >
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          <div
            className={`p-2.5 rounded-xl shrink-0 ${
              detection.severity === 'critical'
                ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
            }`}
          >
            {isDown ? <TrendingDown className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
          </div>
          <div className="space-y-1">
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <h4 className="font-bold text-neutral-900 dark:text-neutral-100 text-sm sm:text-base tracking-tight">
                {detection.kpi_name || 'Metric'} Unexpected {isDown ? 'Decline' : 'Surge'}
              </h4>
              <Badge
                variant={detection.severity === 'critical' ? 'critical' : 'warning'}
                size="xs"
                dot={detection.severity === 'critical'}
              >
                {detection.severity}
              </Badge>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 font-medium">
                {detection.status}
              </span>
              {detection.detected_at && (
                <span className="text-[11px] font-mono text-neutral-500 dark:text-neutral-400 flex items-center space-x-1">
                  <span>•</span>
                  <span>{formatRelativeTime(detection.detected_at)}</span>
                </span>
              )}
            </div>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
              Measured value of <strong className="text-neutral-900 dark:text-neutral-100 font-mono">{(detection.current_value ?? 0).toLocaleString()}</strong> {isDown ? 'dropped' : 'rose'} by{' '}
              <strong className={isDown ? 'text-red-600 dark:text-red-400 font-mono font-bold' : 'text-emerald-600 dark:text-emerald-400 font-mono font-bold'}>
                {formatPercentage(detection.percentage_change)}
              </strong>{' '}
              compared to the 7-day average of <span className="text-neutral-500 font-mono">{(detection.baseline_value ?? 0).toLocaleString()}</span>.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 self-end sm:self-center shrink-0">
          {detection.status === 'active' && onAcknowledge && (
            <Button
              variant="secondary"
              size="xs"
              onClick={() => onAcknowledge(detection.id)}
              leftIcon={<CheckCircle className="w-3.5 h-3.5 text-emerald-600" />}
            >
              Acknowledge
            </Button>
          )}

          {detection.root_causes && detection.root_causes.length > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
              title="Toggle Contributing Factors"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Root Cause Explanations Drawer */}
      {expanded && detection.root_causes && detection.root_causes.length > 0 && (
        <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-[#6B4226] dark:text-[#D5B79F] uppercase tracking-wider font-mono">
              <Layers className="w-3.5 h-3.5" />
              <span>Why this happened (Contributing Factors)</span>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono">Calculated from Business Data</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {detection.root_causes.map((rc) => (
              <div
                key={rc.id}
                className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 flex items-start justify-between text-xs space-x-3 transition-colors"
              >
                <div className="min-w-0 pr-2">
                  <span className="font-semibold text-neutral-900 dark:text-neutral-100 block leading-snug">
                    {rc.explanation_text}
                  </span>
                  <span className="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1 block font-mono">
                    Category: <strong className="text-neutral-700 dark:text-neutral-300">{rc.dimension_name}</strong> • Segment:{' '}
                    <strong className="text-neutral-700 dark:text-neutral-300">{rc.dimension_value}</strong>
                  </span>
                </div>
                <div className="text-right shrink-0">
                  <span className="px-2.5 py-1 rounded-lg bg-white dark:bg-neutral-800 text-[#6B4226] dark:text-[#D5B79F] font-mono font-bold text-xs border border-neutral-200 dark:border-neutral-700 shadow-2xs inline-block">
                    {(rc.contribution_percentage ?? 0).toFixed(1)}%
                  </span>
                  <span className="text-[9px] text-neutral-400 block mt-0.5 font-mono">share of change</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
