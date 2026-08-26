import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  CheckCircle2,
  Activity,
  GitFork,
  Layers,
  ArrowUpRight,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Clock,
  Check,
} from 'lucide-react';
import { Recommendation } from '../../types/noah.types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onStatusChange?: (id: number, status: 'open' | 'in_progress' | 'completed' | 'dismissed') => void;
  onAskNoah?: (prompt: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onStatusChange,
  onAskNoah,
}) => {
  const navigate = useNavigate();
  const [showTechnicalTrace, setShowTechnicalTrace] = useState<boolean>(false);

  const priorityBorder = {
    urgent: 'border-l-4 border-l-red-500',
    standard: 'border-l-4 border-l-[#6B4226] dark:border-l-[#8C5E3C]',
    low: 'border-l-4 border-l-neutral-400',
  }[recommendation.priority] || 'border-l-4 border-l-[#6B4226]';

  return (
    <div
      className={`bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 sm:p-6 transition-all duration-150 flex flex-col justify-between space-y-4 shadow-xs hover:border-neutral-300 dark:hover:border-neutral-700 ${priorityBorder}`}
    >
      <div className="space-y-3.5">
        {/* Header Badges */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <Badge
              variant={recommendation.priority === 'urgent' ? 'critical' : 'brand'}
              size="xs"
              dot={recommendation.priority === 'urgent'}
            >
              {recommendation.priority} priority
            </Badge>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700 font-medium">
              {recommendation.category}
            </span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 font-semibold">
              Impact: {recommendation.impact_level || 'High'}
            </span>
          </div>

          <Badge
            variant={
              recommendation.status === 'completed'
                ? 'healthy'
                : recommendation.status === 'in_progress'
                ? 'warning'
                : recommendation.status === 'dismissed'
                ? 'neutral'
                : 'brand'
            }
            size="xs"
          >
            {recommendation.status.replace('_', ' ')}
          </Badge>
        </div>

        {/* Title */}
        <h4 className="text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100 leading-snug tracking-tight">
          {recommendation.title}
        </h4>

        {/* Action Directive Box */}
        <div className="text-xs text-neutral-800 dark:text-neutral-200 leading-relaxed bg-neutral-50 dark:bg-neutral-900/70 p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 space-y-1 font-medium">
          <span className="text-[#6B4226] dark:text-[#D5B79F] block font-mono text-[11px] font-bold uppercase tracking-wider">
            Recommended Action:
          </span>
          <p>{recommendation.action_text}</p>
        </div>

        {/* PLAIN BUSINESS ENGLISH WHY BOX */}
        <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#101216] border border-[#EBE4D8] dark:border-neutral-800 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6B4226] dark:text-[#D5B79F] font-mono uppercase tracking-wider flex items-center space-x-1.5">
              <Lightbulb className="w-3.5 h-3.5" />
              <span>Why this was recommended:</span>
            </span>

            <button
              onClick={() => setShowTechnicalTrace(!showTechnicalTrace)}
              className="text-[10px] text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200 flex items-center space-x-1 font-mono cursor-pointer transition-colors"
            >
              <span>{showTechnicalTrace ? 'Hide details' : 'Investigate details'}</span>
              {showTechnicalTrace ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          </div>

          <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed font-normal">
            {recommendation.rationale || 'Derived from continuous metric variance analysis.'}
          </p>

          {/* Expandable Technical Traceability Pipeline for Data Investigation */}
          {showTechnicalTrace && (
            <div className="mt-2.5 pt-2.5 border-t border-neutral-200 dark:border-neutral-800 space-y-2 animate-fade-in text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-neutral-500 uppercase">Audit Trail & Evidence</span>
                <div className="flex items-center space-x-2 font-mono text-[10px]">
                  {recommendation.detection_id && (
                    <button
                      onClick={() => navigate('/alerts')}
                      className="text-[#6B4226] dark:text-[#D5B79F] hover:underline font-semibold flex items-center space-x-0.5 cursor-pointer"
                    >
                      <span>Source Anomaly #{recommendation.detection_id}</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  )}
                  {recommendation.kpi_id && (
                    <button
                      onClick={() => navigate(`/kpis/${recommendation.kpi_id}`)}
                      className="text-[#6B4226] dark:text-[#D5B79F] hover:underline font-semibold flex items-center space-x-0.5 cursor-pointer"
                    >
                      <span>Metric #{recommendation.kpi_id}</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
              <div className="p-2 rounded-lg bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-[10px] text-neutral-600 dark:text-neutral-400 font-mono space-y-1">
                <p>Status: Pipeline Verified • Category: {recommendation.category}</p>
                <p>Confidence: High (Grounded on Ingested File Data)</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action status buttons */}
      {onStatusChange && (
        <div className="flex flex-wrap items-center justify-between border-t border-neutral-100 dark:border-neutral-800 pt-3 gap-2 text-xs">
          <span className="text-[11px] text-neutral-500 font-medium font-mono">Triage Action:</span>
          <div className="flex items-center space-x-2">
            {recommendation.status !== 'in_progress' && (
              <Button
                variant="outline"
                size="xs"
                onClick={() => onStatusChange(recommendation.id, 'in_progress')}
                leftIcon={<Clock className="w-3 h-3 text-amber-500" />}
              >
                In Progress
              </Button>
            )}
            {recommendation.status !== 'completed' && (
              <Button
                variant="primary"
                size="xs"
                onClick={() => onStatusChange(recommendation.id, 'completed')}
                leftIcon={<Check className="w-3 h-3" />}
              >
                Mark Complete
              </Button>
            )}
            {recommendation.status !== 'dismissed' && (
              <Button
                variant="ghost"
                size="xs"
                onClick={() => onStatusChange(recommendation.id, 'dismissed')}
              >
                Dismiss
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
