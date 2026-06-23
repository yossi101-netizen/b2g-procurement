"use client";

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { useTranslation } from '@/contexts/TranslationContext';

const languages = [
  { code: 'en', name: 'English UK', flag: 'gb' },
  { code: 'en-US', name: 'English US', flag: 'us' },
  { code: 'es', name: 'Spanish', flag: 'es' },
  { code: 'ar', name: 'Arabic', flag: 'sa' },
  { code: 'he', name: 'Hebrew', flag: 'il' },
  { code: 'nl', name: 'Dutch', flag: 'nl' },
  { code: 'fr', name: 'French', flag: 'fr' },
  { code: 'de', name: 'German', flag: 'de' },
  { code: 'it', name: 'Italian', flag: 'it' },
  { code: 'he', name: 'Hebrew', flag: 'il' },
];

export const LanguageSwitcher = () => {
  const { language, setLanguage } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find(lang => lang.code === language) || languages[languages.length - 1];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div ref={dropdownRef} className="fixed bottom-6 right-6 z-[100]">
      <div className="relative">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-4 py-3 rounded-lg shadow-2xl border-2 transition-all duration-300 min-w-[110px]"
          style={{
            background: 'linear-gradient(135deg, #6F4E37 0%, #4A3228 100%)',
            borderColor: '#D4A574',
            color: '#F5E6D3',
          }}
        >
          <img 
            src={`https://flagcdn.com/w40/${currentLanguage.flag}.png`}
            alt={`${currentLanguage.name} flag`}
            className="w-6 h-4 object-cover rounded-sm shadow-sm"
            onError={(e) => {
              // Fallback in case CDN fails
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          <span className="font-serif font-medium text-sm uppercase">{currentLanguage.name}</span>
          <ChevronDown 
            className={`w-4 h-4 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
          />
        </motion.button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 1, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-full right-0 mb-2 min-w-[200px] rounded-lg shadow-2xl border-2 overflow-hidden"
              style={{
                background: 'linear-gradient(135deg, #6F4E37 0%, #4A3228 100%)',
                borderColor: '#D4A574',
              }}
            >
              <div className="py-1">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setLanguage(lang.code);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all duration-200 border-b border-[#5C3F2E]/30 last:border-b-0 ${
                      language === lang.code
                        ? 'bg-[#D4A574]/30 text-[#D4A574] font-serif font-normal'
                        : 'text-[#F5E6D3]/90 hover:bg-[#5C3F2E] hover:text-[#D4A574]'
                    }`}
                  >
                    <img 
                      src={`https://flagcdn.com/w40/${lang.flag}.png`}
                      alt={`${lang.name} flag`}
                      className="w-7 h-5 object-cover rounded-sm shadow-sm"
                      onError={(e) => {
                        // Fallback in case CDN fails
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <span className="font-medium text-sm flex-1">{lang.name}</span>
                    {language === lang.code && (
                      <span className="text-[#D4A574]">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(92, 63, 46, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #D4A574;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #C49464;
        }
      `}} />
    </div>
  );
};

