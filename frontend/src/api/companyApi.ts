import axiosClient from './axiosClient';
import { Company, CompanyUpdatePayload } from '../types/company.types';
import { User } from '../types/user.types';

export interface DetectedBusinessProfile {
  industry?: string;
  currency?: string;
  company_name?: string;
  timezone?: string;
  fiscal_year?: string;
  country?: string;
  business_type?: string;
  source_file?: string;
  rows_count?: number;
  columns_count?: number;
  detected_at?: string;
}

export const companyApi = {
  getCompany: async (): Promise<Company> => {
    const res = await axiosClient.get<Company>('/company');
    return res.data;
  },

  updateCompany: async (payload: CompanyUpdatePayload): Promise<Company> => {
    const res = await axiosClient.put<Company>('/company', payload);
    return res.data;
  },

  getDetectedProfile: async (): Promise<DetectedBusinessProfile> => {
    const res = await axiosClient.get<DetectedBusinessProfile>('/company/detected-profile');
    return res.data;
  },

  autoAdaptCompany: async (): Promise<Company> => {
    const res = await axiosClient.post<Company>('/company/auto-adapt');
    return res.data;
  },

  getUsers: async (): Promise<User[]> => {
    const res = await axiosClient.get<User[]>('/company/users');
    return res.data;
  },

  inviteUser: async (payload: { email: string; role: string; full_name?: string }): Promise<User> => {
    const res = await axiosClient.post<User>('/company/invite', payload);
    return res.data;
  },
};
