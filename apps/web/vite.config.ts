import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { mockApiPlugin } from './src/mock/middleware';

export default defineConfig({
  plugins: [react(), mockApiPlugin()],
  server: {
    port: 5173,
    host: '127.0.0.1',
  },
});
