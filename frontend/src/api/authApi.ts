import axiosClient from './axiosClient';
import { AuthResponse, User } from '../types/user.types';
import { Company } from '../types/company.types';

export interface AdminRegistrationPayload {
  full_name: string;
  phone_number: string;
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  company_name?: string;
  industry?: string;
}

export interface EmployeeRegistrationPayload {
  full_name: string;
  phone_number: string;
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export interface ForgotPasswordRequestPayload {
  identifier: string;
  portal_type: 'admin' | 'employee';
}

export interface ForgotPasswordVerifyPayload {
  identifier: string;
  code: string;
  portal_type: 'admin' | 'employee';
}

export interface ForgotPasswordConfirmPayload {
  identifier: string;
  code: string;
  new_password: string;
  confirm_password: string;
  portal_type: 'admin' | 'employee';
}

export const authApi = {
  registerAdmin: async (payload: AdminRegistrationPayload): Promise<AuthResponse> => {
    const res = await axiosClient.post<AuthResponse>('/auth/register-admin', payload);
    return res.data;
  },

  registerEmployee: async (payload: EmployeeRegistrationPayload): Promise<AuthResponse> => {
    const res = await axiosClient.post<AuthResponse>('/auth/register-employee', payload);
    return res.data;
  },

  register: async (payload: {
    email: string;
    password: string;
    full_name: string;
    company_name?: string;
    industry?: string;
  }): Promise<AuthResponse> => {
    const res = await axiosClient.post<AuthResponse>('/auth/register', payload);
    return res.data;
  },

  login: async (payload: {
    identifier?: string;
    email?: string;
    password: string;
    portal_type?: 'admin' | 'employee';
  }): Promise<AuthResponse> => {
    const res = await axiosClient.post<AuthResponse>('/auth/login', payload);
    return res.data;
  },

  forgotPasswordRequest: async (payload: ForgotPasswordRequestPayload): Promise<{
    success: boolean;
    message: string;
    target: string;
    code_preview?: string;
    expires_in_minutes: number;
  }> => {
    const res = await axiosClient.post('/auth/forgot-password/request', payload);
    return res.data;
  },

  forgotPasswordVerify: async (payload: ForgotPasswordVerifyPayload): Promise<{
    success: boolean;
    valid: boolean;
    message: string;
  }> => {
    const res = await axiosClient.post('/auth/forgot-password/verify', payload);
    return res.data;
  },

  forgotPasswordConfirm: async (payload: ForgotPasswordConfirmPayload): Promise<{
    success: boolean;
    message: string;
  }> => {
    const res = await axiosClient.post('/auth/forgot-password/confirm', payload);
    return res.data;
  },

  resetPassword: async (payload: { email: string; new_password: string }): Promise<AuthResponse> => {
    const res = await axiosClient.post<AuthResponse>('/auth/reset-password', payload);
    return res.data;
  },

  getMe: async (): Promise<{ user: User; company: Company | null }> => {
    const res = await axiosClient.get<{ user: User; company: Company | null }>('/auth/me');
    return res.data;
  },

  updateProfile: async (payload: {
    full_name?: string;
    email?: string;
    username?: string;
    phone_number?: string;
    password?: string;
  }): Promise<{ user: User; company: Company | null }> => {
    const res = await axiosClient.put<{ user: User; company: Company | null }>('/auth/me', payload);
    return res.data;
  },
};
