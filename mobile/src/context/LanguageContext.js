import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import en from '../translations/en.json';
import es from '../translations/es.json';
import hi from '../translations/hi.json';
import sw from '../translations/sw.json';

const translations = { en, es, hi, sw };
const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState('en');

  useEffect(() => { AsyncStorage.getItem('language').then(v => { if (v && translations[v]) setLanguageState(v); }); }, []);

  async function setLanguage(lang) { if (translations[lang]) { setLanguageState(lang); await AsyncStorage.setItem('language', lang); } }

  function t(key) {
    const keys = key.split('.');
    let value = translations[language] || translations['en'];
    for (const k of keys) { value = value && value[k]; if (value === undefined) { let fb = translations['en']; for (const fk of keys) fb = fb && fb[fk]; return fb || key; } }
    return value || key;
  }

  return <LanguageContext.Provider value={{ language, setLanguage, t }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() { return useContext(LanguageContext); }
