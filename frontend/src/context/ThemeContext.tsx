import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import paletteData from '../theme/palettes.json';

export type Mode = 'system' | 'light' | 'dark';
export type ResolvedMode = 'light' | 'dark';
export type Palette = (typeof paletteData.palettes)[number];
export const palettes: Palette[] = paletteData.palettes;
export const MODES: Mode[] = ['system', 'light', 'dark'];

interface ThemeValue {
  palettes: Palette[];
  paletteId: string;
  setPaletteId: (id: string) => void;
  mode: Mode;
  setMode: (m: Mode) => void;
  resolvedMode: ResolvedMode;
  toggleMode: () => void;
}

const STORAGE_KEY = 'mimir-theme';
const LEGACY_KEY = 'uxintace-theme';
const ThemeContext = createContext<ThemeValue | null>(null);

const readStored = (): { palette?: string; mode?: Mode } => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (saved) return saved;
    const legacy = localStorage.getItem(LEGACY_KEY); // palette id saved by the previous theme switcher
    return legacy ? { palette: legacy, mode: 'dark' } : {};
  } catch {
    return {};
  }
};

const systemPrefersLight = (): boolean =>
  typeof window !== 'undefined' && Boolean(window.matchMedia?.('(prefers-color-scheme: light)').matches);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const stored = readStored();
  const [paletteId, setPaletteId] = useState<string>(
    stored.palette && palettes.some((p) => p.id === stored.palette) ? stored.palette : paletteData.default.palette,
  );
  const [mode, setMode] = useState<Mode>(stored.mode && MODES.includes(stored.mode) ? stored.mode : 'system');
  const [systemLight, setSystemLight] = useState(systemPrefersLight);

  // Follow OS changes while in "system" mode.
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: light)');
    if (!mq) return undefined;
    const onChange = (e: MediaQueryListEvent) => setSystemLight(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const resolvedMode: ResolvedMode = mode === 'system' ? (systemLight ? 'light' : 'dark') : mode;

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.palette = paletteId;
    root.dataset.mode = resolvedMode;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ palette: paletteId, mode }));
      localStorage.removeItem(LEGACY_KEY);
    } catch {
      /* storage unavailable (private mode) – the choice still applies for this visit */
    }
  }, [paletteId, mode, resolvedMode]);

  const toggleMode = useCallback(() => setMode(resolvedMode === 'dark' ? 'light' : 'dark'), [resolvedMode]);

  const value = useMemo(
    () => ({ palettes, paletteId, setPaletteId, mode, setMode, resolvedMode, toggleMode }),
    [paletteId, mode, resolvedMode, toggleMode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeValue => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
};
