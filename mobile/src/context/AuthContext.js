import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const token = await AsyncStorage.getItem('token');
        const userData = await AsyncStorage.getItem('user');
        if (token && userData) setUser(JSON.parse(userData));
      } catch (e) {} finally { setLoading(false); }
    })();
  }, []);

  async function login(email, password) { const data = await api.login(email, password); setUser(data.user); return data; }
  async function register(userData) { const data = await api.register(userData); setUser(data.user); return data; }
  async function logout() { await api.logout(); setUser(null); }
  async function refreshUser() { try { const data = await api.getMe(); setUser(data.user); await AsyncStorage.setItem('user', JSON.stringify(data.user)); } catch (e) {} }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }
