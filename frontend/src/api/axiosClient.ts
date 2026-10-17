import axios from 'axios';
import { expiredSessionLoginPath, isCurrentSessionAuthorization } from '../utils/authRedirect';

function getApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
  if (!envUrl) {
    return '/api/v1';
  }
  const cleanUrl = envUrl.replace(/\/+$/, '');
  if (cleanUrl.endsWith('/api/v1')) {
    return cleanUrl;
  }
  return `${cleanUrl}/api/v1`;
}

const axiosClient = axios.create({
  baseURL: getApiBaseUrl(),
  // 60-second timeout for large uploads and ML pipeline calculations
  timeout: 60000,
});

// Request interceptor: Attach JWT token automatically & handle FormData boundary
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('datalyze_token');
    if (token && config.headers) {
      if (typeof (config.headers as any).set === 'function') {
        (config.headers as any).set('Authorization', `Bearer ${token}`);
      } else {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    if (config.data instanceof FormData && config.headers) {
      if (typeof (config.headers as any).delete === 'function') {
        (config.headers as any).delete('Content-Type');
        (config.headers as any).delete('content-type');
      } else {
        delete config.headers['Content-Type'];
        delete config.headers['content-type'];
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Auto handle 401 on protected requests without interfering with auth forms
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || '';
    const isAuthEndpoint =
      url.includes('/auth/login') ||
      url.includes('/auth/register') ||
      url.includes('/auth/forgot-password') ||
      url.includes('/auth/invite') ||
      url.includes('/auth/accept-invite');

    const requestAuthorization = error.config?.headers?.get?.('Authorization') ?? error.config?.headers?.Authorization;
    if (error.response && error.response.status === 401 && !isAuthEndpoint &&
        isCurrentSessionAuthorization(requestAuthorization, localStorage.getItem('datalyze_token'))) {
      localStorage.removeItem('datalyze_token');
      localStorage.removeItem('datalyze_user');
      localStorage.removeItem('datalyze_company');
      if (!/^\/login(?:\/|$)/i.test(window.location.pathname)) {
        window.location.replace(expiredSessionLoginPath(
          window.location.pathname + window.location.search + window.location.hash
        ));
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;

