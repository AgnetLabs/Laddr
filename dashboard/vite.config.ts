import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Get API URL from environment or use defaults
// In vite.config.ts, we're in Node.js context, so process.env is available
declare const process: { env: { VITE_API_URL?: string } };
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace(/^http/, 'ws');

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
      },
      '/ws': {
        target: WS_URL,
        ws: true,
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        }
      }
    }
  },
  preview: {
    port: 5173,
    host: '0.0.0.0'
  }
})