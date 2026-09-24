import { useEffect, useId, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, Monitor, Moon, Palette, Sun } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { LANGUAGES } from '../../i18n';
import SegmentedControl from '../ui/SegmentedControl';
import { cn } from '../../utils/cn';

/** Appearance panel: language, light/dark/system mode and colour palette. */
export function SettingsPanelContent() {
  const { t, i18n } = useTranslation();
  const { palettes, paletteId, setPaletteId, mode, setMode } = useTheme();

  return (
    <div className="flex flex-col gap-5">
      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">{t('settings.language')}</h3>
        <SegmentedControl
          label={t('settings.language')}
          value={i18n.resolvedLanguage ?? 'hu'}
          onChange={(lng) => i18n.changeLanguage(lng)}
          options={LANGUAGES.map((l) => ({ value: l.code, label: l.label }))}
        />
      </section>

      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">{t('settings.mode')}</h3>
        <SegmentedControl
          label={t('settings.mode')}
          value={mode}
          onChange={setMode}
          options={[
            { value: 'system', label: t('settings.modes.system'), icon: Monitor },
            { value: 'light', label: t('settings.modes.light'), icon: Sun },
            { value: 'dark', label: t('settings.modes.dark'), icon: Moon },
          ]}
        />
      </section>

      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">{t('settings.palette')}</h3>
        <div role="radiogroup" aria-label={t('settings.palette')} className="grid grid-cols-2 gap-2">
          {palettes.map((p) => {
            const active = p.id === paletteId;
            const name = t(`settings.palettes.${p.id}`);
            return (
              <button
                key={p.id}
                type="button"
                role="radio"
                aria-checked={active}
                aria-label={t('settings.selectPalette', { name })}
                onClick={() => setPaletteId(p.id)}
                className={cn(
                  'relative flex flex-col gap-2 rounded-xl border p-2 text-left transition-colors',
                  active ? 'border-accent bg-surface/70' : 'border-border/40 hover:bg-surface/50',
                )}
              >
                {/* Dual swatch: light half | dark half */}
                <span className="flex h-8 overflow-hidden rounded-lg border border-border/40" aria-hidden="true">
                  {(['light', 'dark'] as const).map((m) => (
                    <span key={m} className="flex flex-1 items-center justify-center gap-1" style={{ backgroundColor: p[m].bg }}>
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: p[m].primary }} />
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: p[m].accent }} />
                    </span>
                  ))}
                </span>
                <span className="text-xs font-medium leading-tight text-textMain">{name}</span>
                {active && (
                  <span className="absolute right-1.5 top-1.5 rounded-full bg-primary p-0.5 text-onPrimary">
                    <Check size={10} strokeWidth={3} aria-hidden="true" />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}

/** Navbar button that opens the appearance popover. Closes on outside click and Escape. */
export default function SettingsMenu() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t('settings.open')}
        title={t('settings.open')}
        className="flex h-9 w-9 items-center justify-center rounded-full text-textMain/80 transition-colors hover:bg-surface/60 hover:text-accent"
      >
        <Palette size={18} aria-hidden="true" />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            id={panelId}
            role="dialog"
            aria-label={t('settings.title')}
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-12 z-50 w-80 rounded-2xl border border-border/40 bg-background/95 p-5 shadow-glass backdrop-blur-xl"
          >
            <SettingsPanelContent />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
