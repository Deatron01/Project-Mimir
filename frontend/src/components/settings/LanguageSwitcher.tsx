import { useTranslation } from 'react-i18next';
import { LANGUAGES } from '../../i18n';
import { cn } from '../../utils/cn';

/** Compact HU | EN switch for the navbar. */
export default function LanguageSwitcher({ className }: { className?: string }) {
  const { t, i18n } = useTranslation();
  return (
    <div role="group" aria-label={t('settings.language')} className={cn('flex items-center rounded-full border border-border/50 p-0.5', className)}>
      {LANGUAGES.map((l) => {
        const active = i18n.resolvedLanguage === l.code;
        return (
          <button
            key={l.code}
            type="button"
            lang={l.code}
            aria-pressed={active}
            aria-label={l.label}
            onClick={() => i18n.changeLanguage(l.code)}
            className={cn(
              'rounded-full px-2.5 py-1 text-xs font-bold transition-colors',
              active ? 'bg-primary text-onPrimary' : 'text-muted hover:text-textMain',
            )}
          >
            {l.short}
          </button>
        );
      })}
    </div>
  );
}
