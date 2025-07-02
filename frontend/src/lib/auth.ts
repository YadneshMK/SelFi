import { create } from 'zustand';
import api from './api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, full_name?: string, pan?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    try {
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      localStorage.setItem('access_token', response.data.access_token);
      
      // Also set cookie for middleware to work properly
      document.cookie = `auth-token=${response.data.access_token}; path=/; samesite=lax`;
      
      // Get user info
      const userResponse = await api.get('/auth/me');
      set({ user: userResponse.data, isAuthenticated: true });
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  register: async (email: string, username: string, password: string, full_name?: string, pan?: string) => {
    await api.post('/auth/register', {
      email,
      username,
      password,
      full_name,
      pan
    });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    // Also clear the auth cookie
    document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ user: null, isAuthenticated: false });
      return;
    }
    
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, isAuthenticated: true });
      
      // Ensure cookie is also set if we have a valid token
      document.cookie = `auth-token=${token}; path=/; samesite=lax`;
    } catch {
      localStorage.removeItem('access_token');
      document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
      set({ user: null, isAuthenticated: false });
    }
  }
}));