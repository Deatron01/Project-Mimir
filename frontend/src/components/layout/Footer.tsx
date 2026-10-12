import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

/** Site footer. `compact` (inside the app) keeps only the legal links on one line. */
export default function Footer({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  const year = new Date().getFullYear();
  const links = [
    { to: '/privacy', label: t('footer.privacy') },
    { to: '/terms', label: t('footer.terms') },
    { to: '/data', label: t('footer.yourData') },
    { to: '/contact', label: t('footer.contact') },
  ];

  if (compact) {
    return (
      // Extra bottom padding on phones keeps the links clear of the class tab bar.
      <footer className="border-t border-border/30 bg-background/60 pb-24 pt-5 md:pb-5">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-xs text-muted sm:flex-row md:px-6">
          <span>{t('footer.rights', { year })}</span>
          <nav aria-label={t('footer.links')} className="flex flex-wrap justify-center gap-x-5 gap-y-2">
            {links.map((l) => (
              <Link key={l.to} to={l.to} className="transition-colors hover:text-accent">
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    );
  }

  return (
    <footer className="mt-24 border-t border-border/40 bg-background py-12">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 px-6 md:flex-row">
        <div className="flex flex-col gap-2">
          <span className="text-xl font-extrabold tracking-tight text-textMain">Mimir</span>
          <p className="max-w-sm text-sm leading-relaxed text-muted">{t('footer.tagline')}</p>
        </div>

        <nav aria-label={t('footer.links')} className="grid grid-cols-2 gap-x-10 gap-y-3 text-sm text-muted">
          {links.map((l) => (
            <Link key={l.to} to={l.to} className={cn('transition-colors hover:text-accent')}>
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="mx-auto mt-10 max-w-7xl px-6 text-center text-xs text-muted md:text-left">{t('footer.rights', { year })}</div>
    </footer>
  );
}
