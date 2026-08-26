import axiosClient from './axiosClient';
import { InventoryDashboardSummary } from '../types/inventory.types';

export const inventoryApi = {
  getInventorySummary: async (): Promise<InventoryDashboardSummary> => {
    const res = await axiosClient.get<InventoryDashboardSummary>('/inventory/summary');
    return res.data;
  },

  approveTransfer: async (itemId: number, quantity: number = 50): Promise<{ status: string; message: string }> => {
    const res = await axiosClient.post<{ status: string; message: string }>(
      `/inventory/transfers/${itemId}/approve?quantity=${quantity}`
    );
    return res.data;
  },

  reseedSample: async (): Promise<InventoryDashboardSummary> => {
    const res = await axiosClient.post<InventoryDashboardSummary>('/inventory/reseed-sample');
    return res.data;
  },
};
