import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const ThemeContext = createContext();

export const lightTheme = {
  dark: false, primary: '#16a34a', secondary: '#ff6b35', background: '#f8fafb',
  card: '#ffffff', text: '#1f2937', textSecondary: '#6b7280', border: '#e5e7eb',
  success: '#10b981', warning: '#fbbf24', danger: '#ef4444', info: '#3b82f6',
};

export const darkTheme = {
  dark: true, primary: '#22c55e', secondary: '#ff6b35', background: '#0f172a',
  card: '#1e293b', text: '#f1f5f9', textSecondary: '#94a3b8', border: '#334155',
  success: '#10b981', warning: '#fbbf24', danger: '#ef4444', info: '#3b82f6',
};

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(false);
  const theme = isDark ? darkTheme : lightTheme;

  useEffect(() => { AsyncStorage.getItem('theme').then(v => { if (v === 'dark') setIsDark(true); }); }, []);

  async function toggleTheme() { const n = !isDark; setIsDark(n); await AsyncStorage.setItem('theme', n ? 'dark' : 'light'); }

  return <ThemeContext.Provider value={{ theme, isDark, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() { return useContext(ThemeContext); }
