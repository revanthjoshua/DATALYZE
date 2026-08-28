import axios from 'axios';

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
  // Never leave the UI waiting indefinitely for a cold or unhealthy deployment.
  timeout: 15000,
});

// Request interceptor: Attach JWT token automatically & handle FormData boundary
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('datalyze_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.data instanceof FormData && config.headers) {
      delete config.headers['Content-Type'];
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
      url.includes('/auth/forgot-password');

    if (error.response && error.response.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('datalyze_token');
      localStorage.removeItem('datalyze_user');
      if (window.location.pathname !== '/login' && !window.location.pathname.startsWith('/login/')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;

