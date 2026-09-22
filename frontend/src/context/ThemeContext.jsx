import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import paletteData from '../theme/palettes.json';

export const palettes = paletteData.palettes;
export const MODES = ['system', 'light', 'dark'];

const STORAGE_KEY = 'mimir-theme';
const LEGACY_KEY = 'uxintace-theme';
const ThemeContext = createContext(null);

const readStored = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (saved) return saved;
    const legacy = localStorage.getItem(LEGACY_KEY); // palette id saved by the previous theme switcher
    return legacy ? { palette: legacy, mode: 'dark' } : {};
  } catch {
    return {};
  }
};

const systemPrefersLight = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: light)').matches;

export const ThemeProvider = ({ children }) => {
  const stored = readStored();
  const [paletteId, setPaletteId] = useState(
    palettes.some((p) => p.id === stored.palette) ? stored.palette : paletteData.default.palette,
  );
  const [mode, setMode] = useState(MODES.includes(stored.mode) ? stored.mode : 'system');
  const [systemLight, setSystemLight] = useState(systemPrefersLight);

  // Follow OS changes while in "system" mode.
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: light)');
    if (!mq) return undefined;
    const onChange = (e) => setSystemLight(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const resolvedMode = mode === 'system' ? (systemLight ? 'light' : 'dark') : mode;

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

export const useTheme = () => useContext(ThemeContext);
