import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await authService.getMe();
      // Backend returns: { message: "...", data: { id, username, ... } }
      const userData = response.data?.data || response.data?.user || response.data;
      if (userData && userData.id) {
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        throw new Error('Invalid user data');
      }
    } catch (error) {
      // Only clear auth if it's a real 401, not a network/CORS error
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        setIsAuthenticated(false);
      } else {
        // Network error, CORS error, etc. — keep the token, assume user is logged in
        // This prevents logout on temporary network issues
        const token = localStorage.getItem('access_token');
        if (token) {
          setIsAuthenticated(true);
        }
        console.warn('Failed to verify user session:', error.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (username, password) => {
    const response = await authService.login({ username, password });
    // Backend returns: { message: "...", data: { user: {...}, access_token: "...", refresh_token: "..." } }
    const responseData = response.data?.data || response.data;
    const { user: userData, access_token, refresh_token } = responseData;

    if (!access_token) {
      throw new Error('No access token received');
    }

    localStorage.setItem('access_token', access_token);
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }
    setUser(userData);
    setIsAuthenticated(true);
    return userData;
  };

  const register = async (username, email, password) => {
    const response = await authService.register({ username, email, password });
    const responseData = response.data?.data || response.data;
    const { user: userData, access_token, refresh_token } = responseData;

    if (!access_token) {
      throw new Error('No access token received');
    }

    localStorage.setItem('access_token', access_token);
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }
    setUser(userData);
    setIsAuthenticated(true);
    return userData;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
