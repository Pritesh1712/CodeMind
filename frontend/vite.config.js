import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // Proxy API calls to the FastAPI backend during development
  // This means /api/* calls go to http://localhost:8000/api/*
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Suppress the large bundle warning (react-syntax-highlighter is large by nature)
  build: {
    chunkSizeWarningLimit: 2000,
  },
})
