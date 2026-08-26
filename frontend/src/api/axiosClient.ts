import axios from 'axios';

const axiosClient = axios.create({
  baseURL: '/api/v1',
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
      url.includes('/auth/reset-password');

    if (error.response && error.response.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('datalyze_token');
      localStorage.removeItem('datalyze_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
