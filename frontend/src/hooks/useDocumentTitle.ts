import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

/** Sets the browser tab title from a `meta.*` translation key and updates it when the language changes. */
export default function useDocumentTitle(key: string) {
  const { t, i18n } = useTranslation();
  useEffect(() => {
    document.title = t(key);
  }, [key, t, i18n.resolvedLanguage]);
}
