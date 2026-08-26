import axiosClient from './axiosClient';
import { Prediction } from '../types/noah.types';

export const predictionApi = {
  getPredictions: async (kpiId: number, horizonDays: number = 7): Promise<Prediction[]> => {
    const res = await axiosClient.get<Prediction[]>(`/predictions/${kpiId}?horizon_days=${horizonDays}`);
    return res.data;
  },

  generateForecasts: async (horizonDays: number = 7): Promise<Prediction[]> => {
    const res = await axiosClient.post<Prediction[]>(`/predictions/generate?horizon_days=${horizonDays}`);
    return res.data;
  },

  listAllPredictions: async (): Promise<Prediction[]> => {
    const res = await axiosClient.get<Prediction[]>('/predictions');
    return res.data;
  },
};
