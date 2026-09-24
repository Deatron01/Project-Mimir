/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// In development the API is proxied to the local gateway, so the app can use relative `/api/v1` URLs.
// With VITE_USE_MOCKS=true (the dev default in v1 mode) the in-browser mock answers instead.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: env.VITE_DEV_PROXY_TARGET || 'http://localhost:80',
          changeOrigin: true,
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            vendor: ['@tanstack/react-query', 'framer-motion', 'i18next', 'react-i18next', 'openapi-fetch'],
          },
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      css: false,
      coverage: { provider: 'v8', reporter: ['text-summary', 'lcov'], include: ['src/**/*.{ts,tsx}'], exclude: ['src/api/schema.d.ts', 'src/**/*.stories.tsx', 'src/test/**'] },
    },
  };
});
