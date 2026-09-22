import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// In development the API is proxied to the local gateway, so the app can use relative `/api/v1` URLs.
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
  };
});
