/**
 * API service layer for OSINT Platform
 * Handles all HTTP requests with authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        const refreshResponse = await apiClient.post('/auth/refresh');
        const newToken = refreshResponse.data.access_token;
        localStorage.setItem('access_token', newToken);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.response?.status === 403) {
      toast.error('Access denied. You do not have permission to perform this action.');
    } else if (error.response?.status === 404) {
      toast.error('Resource not found.');
    }

    return Promise.reject(error);
  }
);

// API service interfaces
interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
}

interface User {
  id: string;
  email: string;
  full_name: string;
  company?: string;
  role: string;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

interface DashboardMetrics {
  total_sources: number;
  active_alerts: number;
  recent_analyses: number;
  sentiment_trend: string;
  data_points_collected: number;
}

interface Activity {
  type: string;
  description: string;
  timestamp: string;
}

interface DataSource {
  id: string;
  name: string;
  type: string;
  status: string;
}

interface Alert {
  id: string;
  title: string;
  type: string;
  priority: string;
  created_at: string;
  is_read: boolean;
}

interface Report {
  id: string;
  title: string;
  type: string;
  created_at: string;
  status: string;
}

// API service implementation
export const api = {
  // Authentication endpoints
  auth: {
    login: async (email: string, password: string): Promise<LoginResponse> => {
      const response = await apiClient.post('/auth/login', { email, password });
      return response.data;
    },

    register: async (
      email: string,
      password: string,
      full_name: string,
      company?: string
    ): Promise<LoginResponse> => {
      const response = await apiClient.post('/auth/register', {
        email,
        password,
        full_name,
        company,
      });
      return response.data;
    },

    logout: async (): Promise<void> => {
      await apiClient.post('/auth/logout');
    },

    getCurrentUser: async (): Promise<User> => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    },

    refreshToken: async (): Promise<LoginResponse> => {
      const response = await apiClient.post('/auth/refresh');
      return response.data;
    },

    verifyToken: async (): Promise<{ valid: boolean; user_id: string }> => {
      const response = await apiClient.post('/auth/verify-token');
      return response.data;
    },
  },

  // Dashboard endpoints
  dashboard: {
    getMetrics: async (): Promise<DashboardMetrics> => {
      const response = await apiClient.get('/dashboard/metrics');
      return response.data;
    },

    getRecentActivity: async (): Promise<{ activities: Activity[] }> => {
      const response = await apiClient.get('/dashboard/recent-activity');
      return response.data;
    },
  },

  // Data sources endpoints
  dataSources: {
    list: async (): Promise<{ sources: DataSource[] }> => {
      const response = await apiClient.get('/data-sources');
      return response.data;
    },

    create: async (sourceData: Partial<DataSource>): Promise<DataSource> => {
      const response = await apiClient.post('/data-sources', sourceData);
      return response.data;
    },
  },

  // Analysis endpoints
  analysis: {
    getSentimentAnalysis: async (): Promise<{
      sentiment_score: number;
      confidence: number;
      analysis_date: string;
    }> => {
      const response = await apiClient.get('/analysis/sentiment');
      return response.data;
    },

    triggerAnalysis: async (): Promise<{ message: string; job_id: string }> => {
      const response = await apiClient.post('/analysis/analyze');
      return response.data;
    },
  },

  // Reports endpoints
  reports: {
    list: async (): Promise<{ reports: Report[] }> => {
      const response = await apiClient.get('/reports');
      return response.data;
    },

    generate: async (): Promise<{ message: string; report_id: string }> => {
      const response = await apiClient.post('/reports/generate');
      return response.data;
    },
  },

  // Alerts endpoints
  alerts: {
    list: async (): Promise<{ alerts: Alert[] }> => {
      const response = await apiClient.get('/alerts');
      return response.data;
    },

    create: async (alertData: Partial<Alert>): Promise<{ message: string; alert_id: string }> => {
      const response = await apiClient.post('/alerts', alertData);
      return response.data;
    },
  },

  // Users endpoints
  users: {
    getProfile: async (): Promise<User> => {
      const response = await apiClient.get('/users/profile');
      return response.data;
    },
  },
};

// Health check
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export default api;
