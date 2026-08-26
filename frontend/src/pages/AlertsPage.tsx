import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  RefreshCw,
  CheckCircle2,
  Activity,
  Zap,
} from 'lucide-react';
import { detectionApi } from '../api/detectionApi';
import { DetectionEvent } from '../types/detection.types';
import { DetectionCard } from '../components/detection/DetectionCard';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';

export const AlertsPage: React.FC = () => {
  const toast = useToast();
  const [detections, setDetections] = useState<DetectionEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>(() => {
    return localStorage.getItem('datalyze_alerts_sev') || 'ALL';
  });
  const [statusFilter, setStatusFilter] = useState<string>(() => {
    return localStorage.getItem('datalyze_alerts_stat') || 'ALL';
  });
  const [batchLoading, setBatchLoading] = useState<boolean>(false);

  const fetchDetections = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await detectionApi.getDetections();
      setDetections(Array.isArray(data) ? data : []);
      if (data && data.length > 0 && statusFilter === 'active' && data.filter((d) => (d?.status || '').toLowerCase() === 'active').length === 0) {
        setStatusFilter('ALL');
      }
    } catch (err) {
      console.error('Failed to fetch detections', err);
      setErrorMsg('Failed to load anomaly detection logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetections();
  }, []);

  const handleRefreshPipeline = async () => {
    setRefreshing(true);
    try {
      toast.info('Running z-score statistical anomaly detection...', 'Analysis Pipeline');
      const data = await detectionApi.runDetectionPipeline();
      setDetections(Array.isArray(data) ? data : []);
      toast.success(`Pipeline executed. Found ${data?.length || 0} total detections.`, 'Detection Complete');
    } catch (err) {
      toast.error('Failed to run anomaly detection pipeline.', 'Pipeline Error');
    } finally {
      setRefreshing(false);
    }
  };

  const handleTriggerTestAnomaly = async () => {
    setTestLoading(true);
    try {
      const testDet = await detectionApi.triggerTestAnomaly();
      setDetections((prev) => [testDet, ...(Array.isArray(prev) ? prev : [])]);
      setStatusFilter('ALL');
      toast.success('Simulated critical outlier anomaly generated with root causes!', 'Test Anomaly Triggered');
    } catch (err) {
      toast.error('Failed to generate test anomaly.', 'Error');
    } finally {
      setTestLoading(false);
    }
  };

  const handleSeverityFilter = (sev: string) => {
    setSeverityFilter(sev);
    localStorage.setItem('datalyze_alerts_sev', sev);
  };

  const handleStatusFilter = (st: string) => {
    setStatusFilter(st);
    localStorage.setItem('datalyze_alerts_stat', st);
  };

  const handleAcknowledge = async (detId: number) => {
    try {
      await detectionApi.acknowledgeDetection(detId);
      setDetections((prev) =>
        prev.map((d) => (d.id === detId ? { ...d, status: 'acknowledged' } : d))
      );
      toast.success('Anomaly divergence marked as acknowledged.', 'Alert Triaged');
    } catch (err) {
      console.error('Failed to acknowledge detection', err);
      toast.error('Failed to update alert status.', 'Action Failed');
    }
  };

  const handleMarkAllRead = async () => {
    const activeAlerts = detections.filter((d) => (d?.status || '').toLowerCase() === 'active');
    if (activeAlerts.length === 0) {
      toast.info('There are no active anomalies pending triage.', 'Alert Triage');
      return;
    }

    setBatchLoading(true);
    try {
      const res = await detectionApi.acknowledgeAll();
      setDetections((prev) => prev.map((d) => ({ ...d, status: 'acknowledged' })));
      toast.success(res.message || `Successfully acknowledged all ${activeAlerts.length} active anomalies.`, 'Triage Complete');
    } catch (err) {
      console.error('Failed to acknowledge all alerts', err);
      toast.error('Failed to acknowledge all alerts.', 'Batch Error');
    } finally {
      setBatchLoading(false);
    }
  };

  const filtered = detections.filter((d) => {
    if (!d) return false;
    const dSev = (d.severity || 'medium').toLowerCase();
    const dStat = (d.status || 'active').toLowerCase();
    const matchesSeverity = severityFilter === 'ALL' || dSev === severityFilter.toLowerCase();
    const matchesStatus = statusFilter === 'ALL' || dStat === statusFilter.toLowerCase();
    return matchesSeverity && matchesStatus;
  });

  const activeCount = detections.filter((d) => (d?.status || '').toLowerCase() === 'active').length;
  const criticalCount = detections.filter(
    (d) => (d?.severity || '').toLowerCase() === 'critical' && (d?.status || '').toLowerCase() === 'active'
  ).length;

  const dynamicEyebrow =
    activeCount > 0
      ? `${activeCount} Unresolved • ${criticalCount} Critical`
      : 'All Alerts Triaged • 0 Active';

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<Activity className="w-4 h-4 text-red-500" />}
        title="Anomaly Alerts"
        description="Unusual drops, spikes, and statistical outlier changes detected across your business numbers."
        actions={
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <Button
              variant="outline"
              size="sm"
              isLoading={testLoading}
              onClick={handleTriggerTestAnomaly}
              leftIcon={<Zap className="w-3.5 h-3.5 text-amber-500" />}
            >
              Test Alert (Demo)
            </Button>
            <Button
              variant="secondary"
              size="sm"
              isLoading={batchLoading}
              onClick={handleMarkAllRead}
              disabled={activeCount === 0}
              leftIcon={<CheckCircle className="w-3.5 h-3.5 text-emerald-600" />}
            >
              Mark All as Read ({activeCount})
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={refreshing}
              onClick={handleRefreshPipeline}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />}
            >
              Scan for Alerts
            </Button>
          </div>
        }
      />

      {/* Filter Bar */}
      <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="text-xs font-semibold text-neutral-500 font-mono">Severity:</span>
          {['ALL', 'critical', 'high', 'medium'].map((sev) => (
            <button
              key={sev}
              onClick={() => handleSeverityFilter(sev)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg uppercase tracking-wider transition-colors cursor-pointer ${
                severityFilter === sev
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="text-xs font-semibold text-neutral-500 font-mono">Status:</span>
          {['ALL', 'active', 'acknowledged'].map((st) => (
            <button
              key={st}
              onClick={() => handleStatusFilter(st)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition-colors cursor-pointer ${
                statusFilter === st
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Detections List with 4 States */}
      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchDetections}
        loadingSkeleton="list"
        isEmpty={filtered.length === 0}
        emptyIcon={CheckCircle2}
        emptyTitle="Everything Looks Normal"
        emptyDescription="All your numbers are tracking steadily within expected normal ranges. No unusual drops or spikes were found."
        emptyAction={
          <div className="flex items-center space-x-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.location.href = '/data'}
              leftIcon={<Activity className="w-3.5 h-3.5" />}
            >
              Upload Data to Monitor
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshPipeline}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Scan for Alerts
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {filtered.map((detection) => (
            <DetectionCard
              key={detection.id}
              detection={detection}
              onAcknowledge={handleAcknowledge}
            />
          ))}
        </div>
      </StateView>
    </div>
  );
};
