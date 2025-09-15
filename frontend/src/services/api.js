import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (email, password) => api.post('/api/auth/register', { email, password }),
  getCurrentUser: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
};

export const scrapeAPI = {
  createScrapeJob: (data) => api.post('/api/scrape/', data),
  getScrapeResult: (jobId) => api.get(`/api/scrape/${jobId}`),
  deleteScrapeJob: (jobId) => api.delete(`/api/scrape/${jobId}`),
  exportCSV: (jobId) => api.get(`/api/scrape/${jobId}/export/csv`, { responseType: 'blob' }),
  exportJSON: (jobId) => api.get(`/api/scrape/${jobId}/export/json`, { responseType: 'blob' }),
  exportPDF: (jobId) => api.get(`/api/scrape/${jobId}/export/pdf`, { responseType: 'blob' }),
  exportExcel: (jobId) => api.get(`/api/scrape/${jobId}/export/excel`, { responseType: 'blob' }),
};

export const historyAPI = {
  getHistory: (params) => api.get('/api/history/', { params }),
  getStats: () => api.get('/api/history/stats'),
  clearHistory: (days) => api.delete('/api/history/', { params: { days } }),
};

export default api;
