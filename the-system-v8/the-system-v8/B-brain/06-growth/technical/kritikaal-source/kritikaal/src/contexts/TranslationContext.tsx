"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface TranslationContextType {
  t: (key: string) => string;
  language: string;
  setLanguage: (lang: string) => void;
}

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

// Import translations from separate files
import { translations } from '@/translations';

export const TranslationProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<string>('en');
  const [mounted, setMounted] = useState(false);

  // Only access localStorage after mount (client-side only)
  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem('preferredLanguage');
    if (stored) {
      setLanguageState(stored);
    }
  }, []);

  useEffect(() => {
    if (mounted) {
      localStorage.setItem('preferredLanguage', language);
      document.documentElement.setAttribute('lang', language);
      document.documentElement.setAttribute('dir', language === 'ar' || language === 'he' ? 'rtl' : 'ltr');
    }
  }, [language, mounted]);

  const setLanguage = (lang: string) => {
    setLanguageState(lang);
  };

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: any = translations[language];
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        // Fallback to English
        value = translations['en'];
        for (const fallbackKey of keys) {
          if (value && typeof value === 'object' && fallbackKey in value) {
            value = value[fallbackKey];
          } else {
            return key;
          }
        }
        break;
      }
    }
    
    return typeof value === 'string' ? value : key;
  };

  return (
    <TranslationContext.Provider value={{ t, language, setLanguage }}>
      {children}
    </TranslationContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslation must be used within TranslationProvider');
  }
  return context;
};
