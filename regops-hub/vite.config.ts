import path from 'node:path';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Databricks Apps serves the frontend and backend behind the same origin in
// production. In dev, Vite proxies /api to the local FastAPI server so
// components can always call relative paths (see src/services/client.ts).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
