import axiosClient from './axiosClient';
import { Alert } from '../types/noah.types';

export const alertApi = {
  getAlerts: async (unreadOnly: boolean = false): Promise<Alert[]> => {
    const res = await axiosClient.get<Alert[]>('/alerts', {
      params: { unread_only: unreadOnly },
    });
    return res.data;
  },

  markAllRead: async (): Promise<{ marked_as_read: number }> => {
    const res = await axiosClient.post<{ marked_as_read: number }>('/alerts/mark-all-read');
    return res.data;
  },
};
