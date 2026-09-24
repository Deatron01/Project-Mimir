import { useTranslation } from 'react-i18next';
import ButtonLink from '../components/ui/ButtonLink';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function NotFound() {
  const { t } = useTranslation();
  useDocumentTitle('meta.notFound');
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 text-center">
      <p className="mb-4 bg-gradient-to-r from-accent to-primary bg-clip-text text-7xl font-extrabold text-transparent">404</p>
      <h1 className="mb-3 text-2xl font-bold">{t('notFound.title')}</h1>
      <p className="mb-8 max-w-md text-muted">{t('notFound.desc')}</p>
      <ButtonLink to="/">{t('notFound.home')}</ButtonLink>
    </div>
  );
}
