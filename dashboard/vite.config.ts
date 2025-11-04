// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// export default defineConfig({
//   plugins: [react()],
//   server: {
//     host: '0.0.0.0',
//     port: 5173,
//     proxy: {
//       '/api': {
//         target: process.env.VITE_API_URL || 'http://api:8000',
//         changeOrigin: true,
//       },
//       '/ws': {
//         target: process.env.VITE_WS_URL || 'ws://api:8000',
//         ws: true,
//         changeOrigin: true,
//       }
//     }
//   },
//   build: {
//     outDir: 'dist',
//     emptyOutDir: true,
//     sourcemap: false,
//     rollupOptions: {
//       output: {
//         manualChunks: {
//           vendor: ['react', 'react-dom', 'react-router-dom'],
//           charts: ['recharts'],
//         }
//       }
//     }
//   },
//   preview: {
//     port: 5173,
//     host: '0.0.0.0'
//   }
// })

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Changed from 'http://api:8000' to localhost
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000', // Changed from 'ws://api:8000' to localhost
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