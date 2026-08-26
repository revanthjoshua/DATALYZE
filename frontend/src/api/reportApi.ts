export const reportApi = {
  getKpiSummaryCsvUrl: () => '/api/v1/reports/kpi-summary-csv',
  getKpiTrendCsvUrl: (kpiId: number) => `/api/v1/reports/kpi-trend-csv/${kpiId}`,
};
