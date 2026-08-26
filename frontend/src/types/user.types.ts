export interface User {
  id: number;
  company_id: number;
  email: string;
  username?: string;
  phone_number?: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  company?: {
    id: number;
    name: string;
    industry: string;
    currency: string;
    timezone: string;
  };
}
