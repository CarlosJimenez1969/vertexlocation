import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // 127.0.0.1 (no ::1) y puerto 3000: el rango 5001-52xx lo ocupa Traccar (Java).
    host: '127.0.0.1',
    port: 3000,
    proxy: {
      // El backend local corre en 8001 (el 8000 lo ocupa otro proyecto).
      '/api': { target: 'http://localhost:8001', changeOrigin: true },
      '/uploads': { target: 'http://localhost:8001', changeOrigin: true },
    },
  },
});
