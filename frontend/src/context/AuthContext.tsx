import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, AuthResponse } from '../types/user.types';
import { authApi } from '../api/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (payload: { identifier?: string; email?: string; password: string; portal_type?: 'admin' | 'employee' }) => Promise<User>;
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    company_name?: string;
    industry?: string;
  }) => Promise<void>;
  resetPassword: (payload: { email: string; new_password: string }) => Promise<void>;
  logout: () => void;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('datalyze_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('datalyze_token'));
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize Auth ONLY ONCE on application mount
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('datalyze_token');
      const savedUser = localStorage.getItem('datalyze_user');

      if (savedToken && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          setToken(savedToken);
          
          // Background validation
          const data = await authApi.getMe();
          if (data && data.user) {
            setUser(data.user);
            localStorage.setItem('datalyze_user', JSON.stringify(data.user));
            if (data.company) {
              localStorage.setItem('datalyze_company', JSON.stringify(data.company));
            }
          }
        } catch (err: any) {
          if (err.response && err.response.status === 401) {
            console.warn('Session expired. Logging out.');
            logout();
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const handleAuthSuccess = useCallback((data: AuthResponse): User => {
    localStorage.setItem('datalyze_token', data.access_token);
    localStorage.setItem('datalyze_user', JSON.stringify(data.user));
    if (data.company) {
      localStorage.setItem('datalyze_company', JSON.stringify(data.company));
    }
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const login = async (payload: { identifier?: string; email?: string; password: string; portal_type?: 'admin' | 'employee' }): Promise<User> => {
    const data = await authApi.login(payload);
    return handleAuthSuccess(data);
  };

  const register = async (payload: {
    email: string;
    password: string;
    full_name: string;
    company_name?: string;
    industry?: string;
  }) => {
    const data = await authApi.register(payload);
    handleAuthSuccess(data);
  };

  const resetPassword = async (payload: { email: string; new_password: string }) => {
    const data = await authApi.resetPassword(payload);
    handleAuthSuccess(data);
  };

  const logout = () => {
    const theme = localStorage.getItem('datalyze_theme');
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('datalyze_') && key !== 'datalyze_theme') {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k));
    if (theme) localStorage.setItem('datalyze_theme', theme);
    setToken(null);
    setUser(null);
  };


  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        resetPassword,
        logout,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
