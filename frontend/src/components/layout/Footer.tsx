import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-24 border-t border-border/40 bg-background py-12">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 px-6 md:flex-row">
        <div className="flex flex-col gap-2">
          <span className="text-xl font-bold tracking-tight text-textMain">Mimir</span>
          <p className="max-w-sm text-sm leading-relaxed text-muted">{t('footer.tagline')}</p>
        </div>

        <nav className="flex gap-10 text-sm text-muted">
          <div className="flex flex-col gap-3">
            <Link to="/privacy" className="transition-colors hover:text-accent">
              {t('footer.privacy')}
            </Link>
            <Link to="/terms" className="transition-colors hover:text-accent">
              {t('footer.terms')}
            </Link>
            <Link to="/data" className="transition-colors hover:text-accent">
              {t('footer.yourData')}
            </Link>
          </div>
          <div className="flex flex-col gap-3">
            <Link to="/contact" className="transition-colors hover:text-accent">
              {t('footer.contact')}
            </Link>
          </div>
        </nav>
      </div>
      <div className="mx-auto mt-10 max-w-7xl px-6 text-center text-xs text-muted md:text-left">
        {t('footer.rights', { year })}
      </div>
    </footer>
  );
}
