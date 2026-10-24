import React, { useState, useEffect, useRef } from 'react';
import {
  Download,
  Printer,
  Sparkles,
  Calendar,
  AlertTriangle,
  TrendingUp,
  Lightbulb,
  FileSpreadsheet,
  CheckCircle2,
  FileText,
  Building,
  Activity,
  LineChart,
} from 'lucide-react';
import { reportApi } from '../api/reportApi';
import { kpiApi } from '../api/kpiApi';
import { detectionApi } from '../api/detectionApi';
import { recommendationApi } from '../api/recommendationApi';
import { predictionApi } from '../api/predictionApi';
import { KPISummaryCard } from '../types/kpi.types';
import { DetectionEvent } from '../types/detection.types';
import { Recommendation, Prediction } from '../types/noah.types';
import { useTenant } from '../context/TenantContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { formatKPIValue, formatPercentage } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';

export const ReportsPage: React.FC = () => {
  const { company } = useTenant();
  const { user } = useAuth();
  const toast = useToast();

  const [kpis, setKpis] = useState<KPISummaryCard[]>([]);
  const [detections, setDetections] = useState<DetectionEvent[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [reportPeriod, setReportPeriod] = useState<'30D' | '7D' | '90D'>('30D');
  const requestId = useRef(0);

  const fetchReportData = async () => {
    const request = ++requestId.current;
    try {
      setLoading(true);
      setErrorMsg(null);
      const [kpiData, detData, recData] = await Promise.all([
        kpiApi.getDashboardSummary(reportPeriod),
        detectionApi.getDetections(),
        recommendationApi.getRecommendations(),
      ]);
      if (request !== requestId.current) return;
      setKpis(kpiData);
      setDetections(detData);
      setRecommendations(recData);

    } catch (err) {
      if (request !== requestId.current) return;
      console.error('Failed to load report data', err);
      setErrorMsg('Failed to compile executive briefing.');
    } finally {
      if (request === requestId.current) setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [reportPeriod]);

  const handlePrint = () => {
    toast.info('Preparing print formatted document...', 'Executive Brief');
    setTimeout(() => {
      window.print();
    }, 200);
  };

  const currency = company?.currency || 'USD';
  const currentDateStr = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // Dynamic Executive Narrative Synthesis Engine
  const generateExecutiveNarrative = () => {
    const compName = company?.name || 'Your Enterprise';
    const ind = company?.industry || 'Commercial Business';
    const healthyKpis = kpis.filter((k) => k.status === 'healthy').length;
    const criticalKpis = kpis.filter((k) => k.status === 'critical').length;
    const warningKpis = kpis.filter((k) => k.status === 'warning').length;
    const topAnomaly = detections.find((d) => d.severity === 'critical') || detections[0];
    const topRec = recommendations.find((r) => r.priority === 'urgent') || recommendations[0];

    let healthSummary = '';
    if (criticalKpis > 0) {
      healthSummary = `For ${compName}, ${criticalKpis} of ${kpis.length} metrics have a critical change flag and ${warningKpis} have a warning flag in the selected KPI window. Review changes against the business objective before choosing an action.`;
    } else if (warningKpis > 0) {
      healthSummary = `For ${compName}, ${warningKpis} of ${kpis.length} metrics have a warning flag in the selected KPI window. These flags describe observed changes, not whether business goals were met.`;
    } else {
      healthSummary = `${compName} has ${kpis.length} metrics in this report. No critical or warning change flags are present. This alone does not establish that business goals were met; check data completeness and the saved business brief.`;
    }

    let anomalyNarrative = '';
    if (topAnomaly) {
      anomalyNarrative = `The most significant divergence occurred in ${topAnomaly.kpi_name || 'key metrics'}, shifting ${topAnomaly.direction === 'down' ? 'downward' : 'upward'} by ${Math.abs(topAnomaly.percentage_change || 0).toFixed(1)}% (reading: ${(topAnomaly.current_value || 0).toLocaleString()} vs baseline: ${(topAnomaly.baseline_value || 0).toLocaleString()}).`;
      if (topAnomaly.root_causes && topAnomaly.root_causes.length > 0) {
        anomalyNarrative += ` The recorded contribution for "${topAnomaly.root_causes[0].dimension_value}" (${topAnomaly.root_causes[0].dimension_name}) is ${topAnomaly.root_causes[0].contribution_percentage}% of the net change. This is an arithmetic attribution, not evidence of causation.`;
      }
    } else {
      anomalyNarrative = `No saved anomaly findings are available for the active dataset. Insufficient dated history can also produce an empty result.`;
    }

    let actionNarrative = '';
    if (topRec) {
      actionNarrative = `Suggested investigation: "${topRec.title}" — ${topRec.action_text}`;
    } else {
      actionNarrative = `No saved investigation actions are available. Record decisions, owners, and validation criteria in Analyst Workspace.`;
    }

    return { healthSummary, anomalyNarrative, actionNarrative };
  };

  const [downloadingCsv, setDownloadingCsv] = useState(false);

  const handleDownloadCsv = async () => {
    try {
      setDownloadingCsv(true);
      const cell = (value: unknown) => {
        let text = value === null || value === undefined ? '' : String(value);
        if (typeof value === 'string' && /^[=+\-@\t\r]/.test(text)) text = "'" + text;
        return '"' + text.replace(/"/g, '""') + '"';
      };
      const rows = [['Metric', 'Category', 'Unit', 'Selected window', 'Value', 'Previous', 'Change %', 'Change flag'],
        ...kpis.map(k => [k.name, k.category, k.unit, reportPeriod, k.current_value, k.previous_value, k.percentage_change, k.status])];
      const blob = new Blob(['\uFEFF' + rows.map(row => row.map(cell).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8' });
      reportApi.triggerDownloadBlob(blob, 'datalyze_executive_briefing_report.csv');
      toast.success('Executive KPI summary CSV exported successfully.', 'Export Complete');
    } catch (err: any) {
      toast.error('Failed to download KPI summary report.', 'Download Error');
    } finally {
      setDownloadingCsv(false);
    }
  };

  const narrative = generateExecutiveNarrative();

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in font-sans">
      {/* Header (Hidden in Print) */}
      <div className="no-print">
        <PageHeader
          stage={`Export Ready • ${kpis.length} Monitored Numbers • PDF & CSV Summaries`}
          stageIcon={<FileSpreadsheet className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
          title="Reports & Decision Briefs"
          description="Synthesized executive decision briefings with KPI telemetry, anomaly audit trails, and printable summaries."
          actions={
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDownloadCsv}
                isLoading={downloadingCsv}
                disabled={loading || !!errorMsg || !kpis.length}
                leftIcon={<Download className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />}
              >
                Download CSV
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={handlePrint}
                disabled={loading || !!errorMsg || !kpis.length}
                leftIcon={<Printer className="w-3.5 h-3.5" />}
              >
                Print / Save PDF
              </Button>
            </>
          }
        />
      </div>

      {/* Report Period Filter (Hidden in Print) */}
      <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-3.5 flex items-center justify-between no-print shadow-xs">
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-neutral-400" />
          <span className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 font-mono">
            KPI Window:
          </span>
          <div className="flex items-center space-x-1">
            {(['7D', '30D', '90D'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setReportPeriod(period)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors cursor-pointer ${
                  reportPeriod === period
                    ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                    : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
                }`}
              >
                Latest {period}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-neutral-400 font-mono hidden sm:inline">
          Generated on {currentDateStr}
        </span>
      </div>

      <p className="text-xs text-neutral-500">The KPI window ends at the latest observed data date. Saved findings and investigation actions below refer to the active dataset as a whole. The CSV uses the selected KPI window.</p>

      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchReportData}
        loadingSkeleton="table"
        isEmpty={kpis.length === 0}
        emptyIcon={FileSpreadsheet}
        emptyTitle="No Business Data Available for Briefing"
        emptyDescription="Upload your business spreadsheet or report in the Data Pipeline to generate executive summaries and exportable briefs."
        emptyAction={
          <Button
            variant="primary"
            size="sm"
            onClick={() => window.location.href = '/data'}
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
          >
            Go to Data Pipeline to Upload File
          </Button>
        }
      >
        {/* Printable Executive Document Card */}
        <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 sm:p-10 shadow-sm space-y-8 print:p-0 print:border-none print:shadow-none print:bg-white print:text-black">
          {/* Briefing Top Banner */}
          <div className="border-b border-neutral-200 dark:border-neutral-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <div className="h-7 w-7 rounded-lg bg-[#6B4226] text-white font-bold flex items-center justify-center text-xs">
                  D
                </div>
                <span className="font-bold text-sm tracking-tight">DATALYZE ANALYST WORKSPACE</span>
              </div>
              <h2 className="text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 tracking-tight mt-2">
                Executive Decision Briefing & Operations Review
              </h2>
              <p className="text-xs text-neutral-500 mt-1">
                Prepared for <strong className="text-neutral-800 dark:text-neutral-200">{company?.name || 'Workspace'}</strong> •{' '}
                {company?.industry || 'Enterprise'} Division
              </p>
            </div>

            <div className="text-right text-xs font-mono space-y-1">
              <p className="text-neutral-500">Date: {currentDateStr}</p>
              <p className="text-neutral-500">Author: {user?.full_name || 'System Admin'}</p>
              <Badge variant="healthy" size="xs">
                WORKSPACE REPORT • VALIDATE BEFORE ACTION
              </Badge>
            </div>
          </div>

          {/* Section 0: Executive Narrative Synthesis */}
          <div className="p-5 rounded-xl bg-[#FAF8F5] dark:bg-[#101216] border border-[#EBE4D8] dark:border-neutral-800 space-y-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-neutral-900 dark:text-neutral-100">
                Executive Synthesis & Key Takeaways
              </h3>
            </div>
            <div className="space-y-2 text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed font-sans">
              <p>
                <strong>Operational Summary:</strong> {narrative.healthSummary}
              </p>
              <p>
                <strong>Anomaly Findings:</strong> {narrative.anomalyNarrative}
              </p>
              <p>
                <strong>Recommended Next Steps:</strong> {narrative.actionNarrative}
              </p>
            </div>
          </div>

          {/* Section 1: KPI Telemetry Matrix */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-neutral-900 dark:text-neutral-100">
                1. KPI Telemetry Matrix
              </h3>
            </div>

            <div className="overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 text-neutral-500">
                    <th className="py-2.5 px-3 font-semibold text-[11px] uppercase">Metric</th>
                    <th className="py-2.5 px-3 font-semibold text-[11px] uppercase">Category</th>
                    <th className="py-2.5 px-3 font-semibold text-[11px] uppercase text-right">Current</th>
                    <th className="py-2.5 px-3 font-semibold text-[11px] uppercase text-right">Δ Delta</th>
                    <th className="py-2.5 px-3 font-semibold text-[11px] uppercase text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/60 font-mono">
                  {kpis.map((kpi) => (
                    <tr key={kpi.id}>
                      <td className="py-2 px-3 font-sans font-bold text-neutral-900 dark:text-neutral-100">
                        {kpi.name}
                      </td>
                      <td className="py-2 px-3">
                        <Badge variant="brand" size="xs">
                          {kpi.category}
                        </Badge>
                      </td>
                      <td className="py-2 px-3 text-right font-bold text-neutral-900 dark:text-neutral-100">
                        {formatKPIValue(kpi.current_value, kpi.unit, currency)}
                      </td>
                      <td className="py-2 px-3 text-right">
                        {kpi.percentage_change !== null && kpi.percentage_change !== undefined ? (
                          <span
                            className={`font-semibold ${
                              kpi.percentage_change >= 0 ? 'text-emerald-600' : 'text-red-600'
                            }`}
                          >
                            {formatPercentage(kpi.percentage_change)}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-2 px-3 text-center">
                        <Badge
                          variant={
                            kpi.status === 'healthy'
                              ? 'healthy'
                              : kpi.status === 'warning'
                              ? 'warning'
                              : 'critical'
                          }
                          size="xs"
                        >
                          {kpi.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Active Anomalies */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-neutral-900 dark:text-neutral-100">
                2. Statistical Anomalies & Baseline Changes
              </h3>
            </div>

            {detections.length === 0 ? (
              <p className="text-xs text-neutral-500 italic">No statistical anomalies detected.</p>
            ) : (
              <div className="space-y-2">
                {detections.slice(0, 4).map((det) => (
                  <div
                    key={det.id}
                    className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-neutral-900 dark:text-neutral-100">
                        {det.kpi_name || 'Metric'} Baseline Divergence ({det.direction.toUpperCase()})
                      </span>
                      <Badge
                        variant={
                          det.severity === 'critical'
                            ? 'critical'
                            : det.severity === 'high'
                            ? 'warning'
                            : 'info'
                        }
                        size="xs"
                      >
                        {det.severity}
                      </Badge>
                    </div>
                    <p className="text-neutral-600 dark:text-neutral-400 font-sans">
                      Reading of {det.current_value} diverged by {formatPercentage(det.percentage_change)} from baseline ({det.baseline_value}).
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 3: Recommended Directives */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Lightbulb className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-neutral-900 dark:text-neutral-100">
                3. Suggested Investigation Actions
              </h3>
            </div>

            {recommendations.length === 0 ? (
              <p className="text-xs text-neutral-500 italic">No open prescriptions pending.</p>
            ) : (
              <div className="space-y-2">
                {recommendations.slice(0, 4).map((rec) => (
                  <div
                    key={rec.id}
                    className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-neutral-900 dark:text-neutral-100">
                        {rec.title}
                      </span>
                      <Badge variant="brand" size="xs">
                        {rec.priority}
                      </Badge>
                    </div>
                    <p className="text-neutral-600 dark:text-neutral-400 font-sans">
                      {rec.action_text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </StateView>
    </div>
  );
};
