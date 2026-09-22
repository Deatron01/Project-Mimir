import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import hu from './locales/hu/translation.json';
import en from './locales/en/translation.json';

export const LANGUAGES = [
  { code: 'hu', label: 'Magyar', short: 'HU' },
  { code: 'en', label: 'English', short: 'EN' },
];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { hu: { translation: hu }, en: { translation: en } },
    supportedLngs: ['hu', 'en'],
    nonExplicitSupportedLngs: true,
    fallbackLng: 'hu',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'mimir-lang',
      caches: ['localStorage'],
    },
    returnNull: false,
  });

const syncHtmlLang = (lng) => {
  document.documentElement.lang = lng?.startsWith('en') ? 'en' : 'hu';
};
syncHtmlLang(i18n.resolvedLanguage);
i18n.on('languageChanged', syncHtmlLang);

export default i18n;
