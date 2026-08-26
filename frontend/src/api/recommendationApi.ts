import axiosClient from './axiosClient';
import { Recommendation } from '../types/noah.types';

export const recommendationApi = {
  getRecommendations: async (): Promise<Recommendation[]> => {
    const res = await axiosClient.get<Recommendation[]>('/recommendations');
    return res.data;
  },

  generateRecommendations: async (): Promise<Recommendation[]> => {
    const res = await axiosClient.post<Recommendation[]>('/recommendations/generate');
    return res.data;
  },

  updateStatus: async (
    recId: number,
    status: 'open' | 'in_progress' | 'completed' | 'dismissed'
  ): Promise<Recommendation> => {
    const res = await axiosClient.post<Recommendation>(`/recommendations/${recId}/status?status=${status}`);
    return res.data;
  },
};
