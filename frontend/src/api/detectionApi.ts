import axiosClient from './axiosClient';
import { DetectionEvent, RootCauseResult } from '../types/detection.types';

export const detectionApi = {
  getDetections: async (limit: number = 50): Promise<DetectionEvent[]> => {
    const res = await axiosClient.get<DetectionEvent[]>(`/detections?limit=${limit}`);
    return res.data;
  },

  runDetectionPipeline: async (): Promise<DetectionEvent[]> => {
    const res = await axiosClient.post<DetectionEvent[]>('/detections/run');
    return res.data;
  },

  acknowledgeDetection: async (detectionId: number): Promise<DetectionEvent> => {
    const res = await axiosClient.post<DetectionEvent>(`/detections/${detectionId}/acknowledge`);
    return res.data;
  },

  acknowledgeAll: async (): Promise<{ message: string; acknowledged_count: number }> => {
    const res = await axiosClient.post<{ message: string; acknowledged_count: number }>('/detections/acknowledge-all');
    return res.data;
  },

  triggerTestAnomaly: async (): Promise<DetectionEvent> => {
    const res = await axiosClient.post<DetectionEvent>('/detections/test-anomaly');
    return res.data;
  },

  getRootCauses: async (detectionId: number): Promise<RootCauseResult[]> => {
    const res = await axiosClient.get<RootCauseResult[]>(`/detections/${detectionId}/root-causes`);
    return res.data;
  },
};
