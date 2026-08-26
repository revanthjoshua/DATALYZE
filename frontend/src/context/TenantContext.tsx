import React, { createContext, useContext, useState, useEffect } from 'react';
import { Company, CompanyUpdatePayload } from '../types/company.types';
import { companyApi } from '../api/companyApi';
import { useAuth } from './AuthContext';

interface TenantContextType {
  company: Company | null;
  loading: boolean;
  refreshCompany: () => Promise<void>;
  updateCompany: (payload: CompanyUpdatePayload) => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, user } = useAuth();
  const [company, setCompany] = useState<Company | null>(() => {
    const saved = localStorage.getItem('datalyze_company');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState<boolean>(false);

  const refreshCompany = async () => {
    if (!token || !user) return;
    try {
      setLoading(true);
      const data = await companyApi.getCompany();
      setCompany(data);
      localStorage.setItem('datalyze_company', JSON.stringify(data));
    } catch (err) {
      console.error('Failed to fetch company profile', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && user) {
      refreshCompany();
    } else {
      setCompany(null);
    }
  }, [token, user]);

  const updateCompany = async (payload: CompanyUpdatePayload) => {
    const updated = await companyApi.updateCompany(payload);
    setCompany(updated);
    localStorage.setItem('datalyze_company', JSON.stringify(updated));
  };

  return (
    <TenantContext.Provider value={{ company, loading, refreshCompany, updateCompany }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};
