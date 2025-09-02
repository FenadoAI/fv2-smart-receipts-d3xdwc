import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      // Redirect to login if needed
    }
    return Promise.reject(error);
  }
);

// Receipt API
export const receiptAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post('/receipts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getAll: async (params = {}) => {
    return apiClient.get('/receipts', { params });
  },

  getById: async (id) => {
    return apiClient.get(`/receipts/${id}`);
  },

  update: async (id, data) => {
    return apiClient.put(`/receipts/${id}`, data);
  },

  delete: async (id) => {
    return apiClient.delete(`/receipts/${id}`);
  },
};

// Analytics API
export const analyticsAPI = {
  getSummary: async () => {
    return apiClient.get('/analytics/summary');
  },
};

// Categories API
export const categoriesAPI = {
  getAll: async () => {
    return apiClient.get('/categories');
  },
};

// Export default API client
export default apiClient;