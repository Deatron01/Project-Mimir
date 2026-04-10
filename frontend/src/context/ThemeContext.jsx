import React, { createContext, useContext, useEffect, useState } from 'react';

export const themes = [
  {
    id: 'original',
    name: 'Mimir Eredeti',
    colors: { bg: '#1A2D42', surface: '#2E4156', border: '#AAB7B7', primary: '#C0C8CA', accent: '#D4D8DD', text: '#FFE3D8' }
  },
  {
    id: 'midnight',
    name: 'Midnight Blossom',
    colors: { bg: '#0B1B32', surface: '#0D1E4C', border: '#26415E', primary: '#C48CB3', accent: '#83A6CE', text: '#E5C9D7' }
  },
  {
    id: 'ocean',
    name: 'Deep Ocean',
    colors: { bg: '#031716', surface: '#032F30', border: '#274D60', primary: '#0C969C', accent: '#0A7075', text: '#6BA3BE' }
  },
  {
    id: 'sunset',
    name: 'Sunset Glow',
    colors: { bg: '#1B1931', surface: '#44174E', border: '#662249', primary: '#ED9E59', accent: '#A34054', text: '#E9BCB9' }
  },
  {
    id: 'lavender',
    name: 'Lavender Dream',
    colors: { bg: '#49225B', surface: '#6E3482', border: '#825296', primary: '#A56ABD', accent: '#E7DBEF', text: '#F5EBFA' }
  },
  {
    id: 'forest',
    name: 'Forest Whisper',
    colors: { bg: '#0F2A1D', surface: '#375534', border: '#4C6A48', primary: '#6B9071', accent: '#AEC3B0', text: '#E3EED4' }
  }
];

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [activeThemeId, setActiveThemeId] = useState(() => {
    return localStorage.getItem('uxintace-theme') || 'original';
  });

  useEffect(() => {
    const activeTheme = themes.find(t => t.id === activeThemeId) || themes[0];
    
    // CSS változók injektálása
    const root = document.documentElement;
    root.style.setProperty('--color-bg', activeTheme.colors.bg);
    root.style.setProperty('--color-surface', activeTheme.colors.surface);
    root.style.setProperty('--color-border', activeTheme.colors.border); // <-- BORDER HOZZÁADVA
    root.style.setProperty('--color-primary', activeTheme.colors.primary);
    root.style.setProperty('--color-accent', activeTheme.colors.accent);
    root.style.setProperty('--color-text', activeTheme.colors.text);

    localStorage.setItem('uxintace-theme', activeThemeId);
  }, [activeThemeId]);

  return (
    <ThemeContext.Provider value={{ activeThemeId, setActiveThemeId, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);