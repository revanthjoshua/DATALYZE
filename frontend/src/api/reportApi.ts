import axiosClient from './axiosClient';

export const reportApi = {
  downloadKpiSummaryCsv: async (): Promise<Blob> => {
    const res = await axiosClient.get('/reports/kpi-summary-csv', {
      responseType: 'blob',
    });
    return res.data;
  },

  downloadKpiTrendCsv: async (kpiId: number): Promise<Blob> => {
    const res = await axiosClient.get(`/reports/kpi-trend-csv/${kpiId}`, {
      responseType: 'blob',
    });
    return res.data;
  },

  triggerDownloadBlob: (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
