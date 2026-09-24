import { Moon, Sun } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

/** One-click light/dark switch for the navbar. */
export default function ModeToggle() {
  const { t } = useTranslation();
  const { resolvedMode, toggleMode } = useTheme();
  const next = resolvedMode === 'dark' ? 'light' : 'dark';
  const label = t('settings.toggleMode', { mode: t(`settings.modes.${next}`).toLowerCase() });
  return (
    <button
      type="button"
      onClick={toggleMode}
      aria-label={label}
      title={label}
      className="flex h-9 w-9 items-center justify-center rounded-full text-textMain/80 transition-colors hover:bg-surface/60 hover:text-accent"
    >
      {resolvedMode === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
    </button>
  );
}
