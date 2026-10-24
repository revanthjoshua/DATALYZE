import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UserCheck,
  TrendingUp,
  Bell,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Boxes,
  LineChart,
  ArrowRight,
  RefreshCw,
  Clock,
  Check,
  Shield,
  Layers,
  FileSpreadsheet,
  UploadCloud,
} from 'lucide-react';
import { kpiApi } from '../api/kpiApi';
import { alertApi } from '../api/alertApi';
import { recommendationApi } from '../api/recommendationApi';
import { KPISummaryCard } from '../types/kpi.types';
import { Alert, Recommendation } from '../types/noah.types';
import { useAuth } from '../context/AuthContext';
import { useDateRange } from '../context/DateRangeContext';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { PageHeader } from '../components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { StateView } from '../components/ui/StateView';
import { formatKPIValue } from '../utils/formatters';

export const EmployeeDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { company } = useTenant();
  const toast = useToast();
  const { timeRange } = useDateRange();
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchDashboardData = useCallback(async (isSilent: boolean = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    setError(null);
    try {
      const [kpiData, alertData, recData] = await Promise.all([
        kpiApi.getDashboardSummary(timeRange),
        alertApi.getAlerts(),
        recommendationApi.getRecommendations(),
      ]);

      setKpis(kpiData);
      setAlerts(alertData);
      setRecommendations(recData);
    } catch (err) {
      setError('Could not load your workspace. Retry to view the latest data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleUpdateRecStatus = async (
    recId: number,
    newStatus: 'open' | 'in_progress' | 'completed' | 'dismissed'
  ) => {
    try {
      await recommendationApi.updateStatus(recId, newStatus);
      toast.success(`Action item marked as ${newStatus.replace('_', ' ')}.`, 'Task Updated');
      fetchDashboardData(true);
    } catch (err) {
      toast.error('Failed to update task status.', 'Error');
    }
  };

  const handleAcknowledgeAlerts = async () => {
    try {
      await alertApi.markAllRead();
      toast.success('All active alerts acknowledged.', 'Alerts Updated');
      fetchDashboardData(true);
    } catch (err) {
      toast.error('Failed to acknowledge alerts.', 'Error');
    }
  };

  const currency = company?.currency || 'USD';
  const unreadAlerts = alerts.filter((a) => !a.is_read);
  const activeRecommendations = recommendations.filter((r) => r.status !== 'completed' && r.status !== 'dismissed');
  const hasData = kpis.length > 0 || alerts.length > 0 || recommendations.length > 0;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in font-sans">
      {/* Header */}
      <PageHeader
        stage={`Employee Workspace • ${company?.name || 'Company Operations'}`}
        stageIcon={<UserCheck className="w-4 h-4 text-blue-500" />}
        title={`Welcome, ${user?.full_name || 'Team Member'}`}
        description="Review uploaded metrics, saved recommendations, and detected alerts."
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              isLoading={refreshing}
              onClick={() => fetchDashboardData(true)}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />}
            >
              Refresh Data
            </Button>
            <Badge variant="brand" size="md">
              <UserCheck className="w-3.5 h-3.5 mr-1 inline text-blue-500" /> Employee Mode
            </Badge>
          </div>
        }
      />

      <StateView isLoading={loading} isError={!!error} errorMessage={error || undefined} onRetry={() => fetchDashboardData()} loadingSkeleton="card-grid">
        {!hasData ? (
          <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 sm:p-10 text-center space-y-6 shadow-xs relative overflow-hidden">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="max-w-xl mx-auto space-y-2">
              <h3 className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                No analysis available yet
              </h3>
              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed font-normal">
                No metrics, recommendations, or alerts are available. Upload or review your dataset in Data & Preparation, then explore it in Analyst Workspace.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="md"
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => navigate('/data')}
                leftIcon={<FileSpreadsheet className="w-4 h-4" />}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Open Data & Preparation
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Top Quick Stats Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card className="p-4 border-l-4 border-l-blue-500 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-500 font-semibold block">
                    Tracked Metrics
                  </span>
                  <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100 font-mono mt-1">
                    {kpis.length} Active
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </Card>

              <Card className="p-4 border-l-4 border-l-amber-500 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-500 font-semibold block">
                    Operational Alerts
                  </span>
                  <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100 font-mono mt-1">
                    {unreadAlerts.length} Unread
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600">
                  <Bell className="w-5 h-5" />
                </div>
              </Card>

              <Card className="p-4 border-l-4 border-l-emerald-500 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-500 font-semibold block">
                    Pending Actions
                  </span>
                  <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100 font-mono mt-1">
                    {activeRecommendations.length} Tasks
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600">
                  <Lightbulb className="w-5 h-5" />
                </div>
              </Card>

            </div>

            {/* Key Metric Summary Cards */}
            {kpis.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-blue-500" />
                    <span>Operational Key Performance Metrics</span>
                  </h3>
                  <Link
                    to="/kpis"
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
                  >
                    <span>View All Metrics</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {kpis.slice(0, 6).map((kpi) => (
                    <Card key={kpi.id} className="p-4 space-y-3 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 truncate">
                          {kpi.name}
                        </span>
                        <Badge
                          variant={
                            kpi.percentage_change == null ? 'neutral' : kpi.status === 'healthy'
                              ? 'healthy'
                              : kpi.status === 'warning'
                              ? 'warning'
                              : 'critical'
                          }
                          size="xs"
                          dot
                        >
                          {kpi.percentage_change == null ? 'No comparison' : kpi.status}
                        </Badge>
                      </div>

                      <div className="flex items-baseline justify-between">
                        <span className="text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 font-mono">
                          {formatKPIValue(kpi.current_value, kpi.unit, currency)}
                        </span>
                        {kpi.percentage_change !== null && kpi.percentage_change !== undefined && (
                          <span
                            className={`text-xs font-mono font-bold ${
                              kpi.percentage_change >= 0
                                ? 'text-emerald-600 dark:text-emerald-400'
                                : 'text-red-600 dark:text-red-400'
                            }`}
                          >
                            {kpi.percentage_change >= 0 ? '+' : ''}
                            {kpi.percentage_change.toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Operational Tasks & Recommendations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center space-x-2">
                    <Lightbulb className="w-4 h-4 text-emerald-500" />
                    <span>Recommendations to Review</span>
                  </h3>
                  <Link
                    to="/recommendations"
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    View All →
                  </Link>
                </div>

                <div className="space-y-3">
                  {recommendations.slice(0, 4).map((rec) => (
                    <Card
                      key={rec.id}
                      className={`p-4 space-y-2 border-l-4 ${
                        rec.status === 'completed'
                          ? 'border-l-emerald-500 opacity-75'
                          : rec.priority === 'urgent'
                          ? 'border-l-red-500'
                          : 'border-l-blue-500'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
                          {rec.title}
                        </span>
                        <Badge
                          variant={
                            rec.status === 'completed'
                              ? 'healthy'
                              : rec.priority === 'urgent'
                              ? 'critical'
                              : 'neutral'
                          }
                          size="xs"
                        >
                          {rec.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                        {rec.action_text}
                      </p>
                      <div className="flex items-center justify-between pt-2 border-t border-neutral-100 dark:border-neutral-800">
                        <span className="text-[10px] text-neutral-400 font-mono uppercase">
                          Impact: {rec.impact_level || 'Not estimated'}
                        </span>
                        {rec.status !== 'completed' && (
                          <Button
                            variant="secondary"
                            size="xs"
                            onClick={() => handleUpdateRecStatus(rec.id, 'completed')}
                            leftIcon={<Check className="w-3 h-3 text-emerald-600" />}
                          >
                            Mark Complete
                          </Button>
                        )}
                      </div>
                    </Card>
                  ))}
                  {recommendations.length === 0 && (
                    <Card className="p-6 text-center text-xs text-neutral-500">
                      No recommendations are saved for the current dataset.
                    </Card>
                  )}
                </div>
              </div>

              {/* Active Anomaly Alerts */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center space-x-2">
                    <Bell className="w-4 h-4 text-amber-500" />
                    <span>Recorded Alerts ({unreadAlerts.length})</span>
                  </h3>
                  {unreadAlerts.length > 0 && (
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={handleAcknowledgeAlerts}
                      className="text-xs text-blue-600 dark:text-blue-400"
                    >
                      Acknowledge All
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  {alerts.slice(0, 4).map((alert) => (
                    <Card
                      key={alert.id}
                      className={`p-4 space-y-2 border-l-4 ${
                        alert.severity === 'critical' ? 'border-l-red-500' : 'border-l-amber-500'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
                          {alert.title}
                        </span>
                        <Badge variant={alert.severity === 'critical' ? 'critical' : 'warning'} size="xs">
                          {alert.severity}
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                        {alert.message}
                      </p>
                    </Card>
                  ))}
                  {alerts.length === 0 && (
                    <Card className="p-6 text-center text-xs text-neutral-500">
                      No anomaly alerts are available. This does not establish that the dataset is free of issues.
                    </Card>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </StateView>
    </div>
  );
};
