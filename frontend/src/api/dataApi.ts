import axiosClient from './axiosClient';
import { IngestionResponse } from '../types/data.types';

export const dataApi = {
  uploadFile: async (file: File): Promise<IngestionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axiosClient.post<IngestionResponse>('/data/upload', formData);
    return res.data;
  },

  ingestRawData: async (payload: any): Promise<IngestionResponse> => {
    const res = await axiosClient.post<IngestionResponse>('/data/ingest-raw', payload);
    return res.data;
  },

  updateDataset: async (records: any[], filename?: string): Promise<IngestionResponse> => {
    const res = await axiosClient.put<IngestionResponse>('/data/dataset', {
      records,
      filename: filename || 'edited_dataset.csv',
    });
    return res.data;
  },

  loadSampleDataset: async (): Promise<IngestionResponse> => {
    const res = await axiosClient.post<IngestionResponse>('/data/load-sample');
    return res.data;
  },

  getDatasetInfo: async (): Promise<any> => {
    const res = await axiosClient.get('/data/dataset/info');
    return res.data;
  },

  getDatasetPreview: async (limit: number = 50, offset: number = 0): Promise<any> => {
    const res = await axiosClient.get('/data/dataset/preview', {
      params: { limit, offset },
    });
    return res.data;
  },

  queryDataset: async (payload: any): Promise<any> => {
    const res = await axiosClient.post('/data/dataset/query', payload);
    return res.data;
  },

  runInteractiveQuery: async (payload: any): Promise<any> => {
    const res = await axiosClient.post('/data/dataset/query', payload);
    return res.data;
  },

  getSampleCsvUrl: (templateType: string = 'retail'): string => {
    return `/api/v1/data/sample-csv?type=${templateType}`;
  },

  getDatasetDownloadUrl: (): string => {
    return `/api/v1/data/dataset/download`;
  },
};
