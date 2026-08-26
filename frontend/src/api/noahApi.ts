import axiosClient from './axiosClient';
import { NoahQueryResponse, NoahAgenticPlanResponse } from '../types/noah.types';

export const noahApi = {
  askNoah: async (payload: { question: string; kpi_id?: number; time_frame?: string }): Promise<NoahQueryResponse> => {
    const res = await axiosClient.post<NoahQueryResponse>('/noah/query', payload);
    return res.data;
  },

  runAgenticReasoning: async (payload: { goal: string; kpi_id?: number }): Promise<NoahAgenticPlanResponse> => {
    const res = await axiosClient.post<NoahAgenticPlanResponse>('/noah/agentic-reasoning', payload);
    return res.data;
  },
};
