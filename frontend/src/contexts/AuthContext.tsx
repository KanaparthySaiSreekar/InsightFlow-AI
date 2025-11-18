'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '@/lib/api';
import { User } from '@/types';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const response = await authAPI.getCurrentUser();
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('access_token');
      }
    }
    setLoading(false);
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      localStorage.setItem('access_token', response.data.access_token);
      await checkAuth();
      toast.success('Logged in successfully!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed');
      throw error;
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      await authAPI.signup(email, password);
      toast.success('Account created! Please log in.');
      router.push('/login');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Signup failed');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    toast.success('Logged out successfully');
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
