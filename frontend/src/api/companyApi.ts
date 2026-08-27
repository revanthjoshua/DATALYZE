import axiosClient from './axiosClient';
import { Company, CompanyUpdatePayload } from '../types/company.types';
import { User, Invitation } from '../types/user.types';

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

  getInvitations: async (status?: string): Promise<Invitation[]> => {
    const res = await axiosClient.get<Invitation[]>('/company/invitations', {
      params: status ? { status } : undefined,
    });
    return res.data;
  },

  inviteUser: async (payload: { email: string; role: string; full_name?: string }): Promise<Invitation> => {
    const res = await axiosClient.post<Invitation>('/company/invite', payload);
    return res.data;
  },

  resendInvitation: async (id: number): Promise<Invitation> => {
    const res = await axiosClient.post<Invitation>(`/company/invitations/${id}/resend`);
    return res.data;
  },

  revokeInvitation: async (id: number): Promise<Invitation> => {
    const res = await axiosClient.post<Invitation>(`/company/invitations/${id}/revoke`);
    return res.data;
  },

  removeUser: async (userId: number): Promise<User> => {
    const res = await axiosClient.delete<User>(`/company/users/${userId}`);
    return res.data;
  },
};

