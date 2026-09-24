import { useEffect } from 'react';
import type { Decorator, Preview } from '@storybook/react-vite';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { initialize, mswLoader } from 'msw-storybook-addon';
import i18n from '../src/i18n';
import '../src/index.css';
import paletteData from '../src/theme/palettes.json';
import { ThemeProvider, useTheme, type Mode } from '../src/context/ThemeContext';
import { AuthProvider } from '../src/context/AuthContext';
import { ToastProvider } from '../src/components/common/Toaster';
import { setConfig } from '../src/config/runtime';
import { makeHandlers } from '../src/mocks/handlers';

setConfig({ apiBaseUrl: '/api/v1', apiMode: 'v1', useMocks: true });
initialize({ onUnhandledRequest: 'bypass' }, makeHandlers('/api/v1'));

function ThemeSync({ palette, mode }: { palette: string; mode: Mode }) {
  const { setPaletteId, setMode } = useTheme();
  useEffect(() => {
    setPaletteId(palette);
    setMode(mode);
  }, [palette, mode, setPaletteId, setMode]);
  return null;
}

function LocaleSync({ locale }: { locale: string }) {
  useEffect(() => {
    void i18n.changeLanguage(locale);
  }, [locale]);
  return null;
}

const withProviders: Decorator = (Story, ctx) => {
  const { palette, mode, locale } = ctx.globals as { palette: string; mode: Mode; locale: string };
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <ThemeProvider>
          <ThemeSync palette={palette} mode={mode} />
          <LocaleSync locale={locale} />
          <ToastProvider>
            <MemoryRouter>
              <div className="min-h-screen bg-background p-6 text-textMain">
                <Story />
              </div>
            </MemoryRouter>
          </ToastProvider>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

const preview: Preview = {
  loaders: [mswLoader],
  decorators: [withProviders],
  globalTypes: {
    palette: {
      description: 'Colour palette',
      toolbar: { title: 'Palette', icon: 'paintbrush', items: paletteData.palettes.map((p) => p.id), dynamicTitle: true },
    },
    mode: { description: 'Light / dark', toolbar: { title: 'Mode', icon: 'mirror', items: ['light', 'dark'], dynamicTitle: true } },
    locale: { description: 'Language', toolbar: { title: 'Language', icon: 'globe', items: ['hu', 'en'], dynamicTitle: true } },
  },
  initialGlobals: { palette: paletteData.default.palette, mode: 'dark', locale: 'hu' },
  parameters: {
    layout: 'fullscreen',
    a11y: { test: 'error' },
    controls: { matchers: { color: /(background|color)$/i } },
  },
};
export default preview;
