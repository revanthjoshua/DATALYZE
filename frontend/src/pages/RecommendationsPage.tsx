import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, Activity, Lightbulb } from 'lucide-react';
import { recommendationApi } from '../api/recommendationApi';
import { Recommendation } from '../types/noah.types';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';

export const RecommendationsPage: React.FC = () => {
  const toast = useToast();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<string>(() => {
    return localStorage.getItem('datalyze_rec_pri') || 'ALL';
  });
  const [statusFilter, setStatusFilter] = useState<string>(() => {
    return localStorage.getItem('datalyze_rec_stat') || 'ALL';
  });

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await recommendationApi.getRecommendations();
      setRecommendations(data);
    } catch (err) {
      console.error('Failed to fetch recommendations', err);
      setErrorMsg('Failed to load operational recommendations from AI reasoner.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handlePriorityFilter = (p: string) => {
    setPriorityFilter(p);
    localStorage.setItem('datalyze_rec_pri', p);
  };

  const handleStatusFilter = (s: string) => {
    setStatusFilter(s);
    localStorage.setItem('datalyze_rec_stat', s);
  };

  const handleStatusChange = async (
    recId: number,
    newStatus: 'open' | 'in_progress' | 'completed' | 'dismissed'
  ) => {
    try {
      const updated = await recommendationApi.updateStatus(recId, newStatus);
      setRecommendations((prev) =>
        prev.map((r) => (r.id === recId ? updated : r))
      );
      toast.success(`Action directive marked as "${newStatus.replace('_', ' ')}".`, 'Initiative Updated');
    } catch (err) {
      console.error('Failed to update recommendation status', err);
      toast.error('Failed to update action status.', 'Action Error');
    }
  };

  const filtered = recommendations.filter((r) => {
    const matchesPriority = priorityFilter === 'ALL' || r.priority === priorityFilter;
    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesPriority && matchesStatus;
  });

  const pendingCount = recommendations.filter((r) => r.status === 'open' || r.status === 'in_progress').length;
  const urgentCount = recommendations.filter((r) => r.priority === 'urgent' && r.status !== 'completed' && r.status !== 'dismissed').length;

  const dynamicEyebrow =
    pendingCount > 0
      ? `${pendingCount} Pending Action${pendingCount === 1 ? '' : 's'}${urgentCount > 0 ? ` • ${urgentCount} Urgent` : ' • Prioritized by Impact'}`
      : 'All Actions Completed • 0 Pending';

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<Lightbulb className="w-4 h-4 text-amber-500" />}
        title="Recommended Actions"
        description="Practical steps and initiatives recommended to improve your business performance."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={fetchRecommendations}
            disabled={loading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh Actions
          </Button>
        }
      />

      {/* Filter Bar */}
      <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="text-xs font-semibold text-neutral-500 font-mono">Priority:</span>
          {['ALL', 'high', 'medium', 'low'].map((pri) => (
            <button
              key={pri}
              onClick={() => handlePriorityFilter(pri)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg uppercase tracking-wider transition-colors cursor-pointer ${
                priorityFilter === pri
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
              }`}
            >
              {pri}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="text-xs font-semibold text-neutral-500 font-mono">Status:</span>
          {['ALL', 'open', 'in_progress', 'completed'].map((st) => (
            <button
              key={st}
              onClick={() => handleStatusFilter(st)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition-colors cursor-pointer ${
                statusFilter === st
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Recommendations List with 4 States */}
      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchRecommendations}
        loadingSkeleton="list"
        isEmpty={filtered.length === 0}
        emptyIcon={CheckCircle2}
        emptyTitle="No Action Steps Needed Right Now"
        emptyDescription="Your business operations are running smoothly. All monitored numbers are on track."
        emptyAction={
          <div className="flex items-center space-x-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.location.href = '/data'}
              leftIcon={<Lightbulb className="w-3.5 h-3.5" />}
            >
              Upload Data to Generate Actions
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchRecommendations}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Scan for New Recommendations
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {filtered.map((recommendation) => (
            <RecommendationCard
              key={recommendation.id}
              recommendation={recommendation}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      </StateView>
    </div>
  );
};
