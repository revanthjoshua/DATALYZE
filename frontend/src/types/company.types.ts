export interface Company {
  id: number;
  name: string;
  industry: string;
  currency: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyUpdatePayload {
  name?: string;
  industry?: string;
  currency?: string;
  timezone?: string;
}
