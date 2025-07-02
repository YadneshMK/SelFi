import axios from 'axios';
import { NetworkError, isNetworkError } from './network-monitor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Request with token to:', config.url);
    } else {
      console.warn('No access token found for request to:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors and network errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if it's a network error
    if (isNetworkError(error)) {
      const networkError = new NetworkError(
        navigator.onLine 
          ? 'Server connection failed. Please check if the server is running.'
          : 'No internet connection. Please check your network.'
      );
      return Promise.reject(networkError);
    }
    
    // Handle timeout
    if (error.code === 'ECONNABORTED') {
      const timeoutError = new NetworkError('Request timed out. Please try again.');
      return Promise.reject(timeoutError);
    }
    
    // Handle auth errors
    if (error.response?.status === 401) {
      console.error('401 Unauthorized error:', {
        url: error.config?.url,
        token: localStorage.getItem('access_token') ? 'Token exists' : 'No token',
        response: error.response?.data
      });
      localStorage.removeItem('access_token');
      document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Retry logic for failed requests
let retryQueue: Array<() => Promise<any>> = [];
let isRefreshing = false;

export const retryFailedRequest = async (originalRequest: any) => {
  if (!navigator.onLine) {
    throw new NetworkError('No internet connection');
  }
  
  return api(originalRequest);
};

export default api;