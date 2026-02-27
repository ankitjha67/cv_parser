import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for user
    const savedEmail = localStorage.getItem('user_email');
    const savedName = localStorage.getItem('user_name');
    if (savedEmail && savedEmail !== 'anonymous') {
      setUser({ email: savedEmail, name: savedName || 'User' });
    }
    setLoading(false);
  }, []);

  const login = async (email, name) => {
    try {
      // Register or login
      await axios.post(`${API}/auth/register`, { email, name });
      localStorage.setItem('user_email', email);
      localStorage.setItem('user_name', name);
      setUser({ email, name });
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
    setUser(null);
  };

  const getAuthHeader = () => {
    return user ? { Authorization: `Bearer ${user.email}` } : {};
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, getAuthHeader }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
