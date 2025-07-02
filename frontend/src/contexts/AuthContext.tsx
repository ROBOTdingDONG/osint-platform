/**
 * Authentication Context for OSINT Platform
 * Manages user authentication state and provides auth methods
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import toast from 'react-hot-toast';
import { api } from '../services/api';

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

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, company?: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const queryClient = useQueryClient();

  // Get user info query
  const { isLoading: userLoading } = useQuery(
    'currentUser',
    () => api.auth.getCurrentUser(),
    {
      enabled: !!localStorage.getItem('access_token'),
      retry: false,
      onSuccess: (userData) => {
        setUser(userData);
        setIsAuthenticated(true);
      },
      onError: () => {
        localStorage.removeItem('access_token');
        setUser(null);
        setIsAuthenticated(false);
      },
    }
  );

  // Login mutation
  const loginMutation = useMutation(
    ({ email, password }: { email: string; password: string }) =>
      api.auth.login(email, password),
    {
      onSuccess: (data) => {
        localStorage.setItem('access_token', data.access_token);
        queryClient.invalidateQueries('currentUser');
        toast.success('Welcome back!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Login failed');
      },
    }
  );

  // Register mutation
  const registerMutation = useMutation(
    ({
      email,
      password,
      fullName,
      company,
    }: {
      email: string;
      password: string;
      fullName: string;
      company?: string;
    }) => api.auth.register(email, password, fullName, company),
    {
      onSuccess: (data) => {
        localStorage.setItem('access_token', data.access_token);
        queryClient.invalidateQueries('currentUser');
        toast.success('Account created successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Registration failed');
      },
    }
  );

  // Logout mutation
  const logoutMutation = useMutation(() => api.auth.logout(), {
    onSettled: () => {
      localStorage.removeItem('access_token');
      setUser(null);
      setIsAuthenticated(false);
      queryClient.clear();
      toast.success('Logged out successfully');
    },
  });

  // Auto-refresh token
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !user) {
      // Token exists but user not loaded, trigger user fetch
      queryClient.invalidateQueries('currentUser');
    }
  }, [queryClient, user]);

  const login = async (email: string, password: string) => {
    await loginMutation.mutateAsync({ email, password });
  };

  const register = async (
    email: string,
    password: string,
    fullName: string,
    company?: string
  ) => {
    await registerMutation.mutateAsync({ email, password, fullName, company });
  };

  const logout = () => {
    logoutMutation.mutate();
  };

  const refreshToken = async () => {
    try {
      const data = await api.auth.refreshToken();
      localStorage.setItem('access_token', data.access_token);
    } catch (error) {
      logout();
    }
  };

  const isLoading = userLoading || loginMutation.isLoading || registerMutation.isLoading;

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
