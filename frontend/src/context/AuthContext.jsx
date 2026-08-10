import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('chatassist_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('chatassist_token') || '');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('chatassist_token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('chatassist_token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      axios.defaults.headers.common['X-User-Id'] = user.id;
      localStorage.setItem('chatassist_user', JSON.stringify(user));
    } else {
      delete axios.defaults.headers.common['X-User-Id'];
      localStorage.removeItem('chatassist_user');
    }
  }, [user]);

  // Fetch logged in user profile on load if token exists
  useEffect(() => {
    if (token && !user) {
      fetchCurrentUser();
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const res = await axios.get('/api/v1/auth/me');
      setUser(res.data);
    } catch (err) {
      console.error('Error fetching current user:', err);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/auth/login', { email, password });
      const { access_token, user: userData } = res.data;
      setToken(access_token);
      setUser(userData);
      return { success: true, user: userData };
    } catch (err) {
      return {
        success: false,
        message: err.response?.data?.detail || 'Invalid email or password'
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/auth/register', { name, email, password, role: 'customer' });
      const { access_token, user: userData } = res.data;
      setToken(access_token);
      setUser(userData);
      return { success: true, user: userData };
    } catch (err) {
      return {
        success: false,
        message: err.response?.data?.detail || 'Registration failed'
      };
    } finally {
      setLoading(false);
    }
  };

  const applyOrganizer = async (organizationName) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/organizer/apply', { organization_name: organizationName });
      if (user) {
        const updatedUser = { ...user, role: 'organizer' };
        setUser(updatedUser);
      }
      return { success: true, message: res.data.message };
    } catch (err) {
      return {
        success: false,
        message: err.response?.data?.detail || 'Failed to apply as organizer'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken('');
    setUser(null);
    localStorage.removeItem('chatassist_token');
    localStorage.removeItem('chatassist_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, applyOrganizer, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
