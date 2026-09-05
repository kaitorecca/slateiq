import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev-only proxy target: the FastAPI service from agent/ (or `npm run mock`).
const target = process.env.VITE_API_TARGET || 'http://localhost:8811'

export default defineConfig({
  base: '/',
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react/jsx-runtime'],
        },
      },
    },
    chunkSizeWarningLimit: 700,
  },
  server: {
    port: Number(process.env.PORT) || 5188,
    strictPort: false,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/clips': { target, changeOrigin: true },
    },
  },
})
