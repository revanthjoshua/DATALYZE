import axiosClient from './axiosClient';
import { KPIDefinition, KPISummaryCard, KPIValue } from '../types/kpi.types';

export const kpiApi = {
  getKPIs: async (activeOnly: boolean = false): Promise<KPIDefinition[]> => {
    const res = await axiosClient.get<KPIDefinition[]>('/kpis', {
      params: { active_only: activeOnly },
    });
    return res.data;
  },

  getDashboardSummary: async (): Promise<KPISummaryCard[]> => {
    const res = await axiosClient.get<KPISummaryCard[]>('/kpis/summary');
    return res.data;
  },

  getKPIDetail: async (kpiId: number): Promise<KPIDefinition> => {
    const res = await axiosClient.get<KPIDefinition>(`/kpis/${kpiId}`);
    return res.data;
  },

  getKPIValues: async (
    kpiId: number,
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<KPIValue[]> => {
    const res = await axiosClient.get<KPIValue[]>(`/kpis/${kpiId}/values`, { params });
    return res.data;
  },

  toggleKPI: async (kpiId: number, isActive: boolean): Promise<KPIDefinition> => {
    const res = await axiosClient.post<KPIDefinition>(`/kpis/${kpiId}/toggle`, null, {
      params: { is_active: isActive },
    });
    return res.data;
  },

  createKPI: async (payload: Partial<KPIDefinition>): Promise<KPIDefinition> => {
    const res = await axiosClient.post<KPIDefinition>('/kpis', payload);
    return res.data;
  },

  updateKPI: async (kpiId: number, payload: Partial<KPIDefinition>): Promise<KPIDefinition> => {
    const res = await axiosClient.put<KPIDefinition>(`/kpis/${kpiId}`, payload);
    return res.data;
  },
};
