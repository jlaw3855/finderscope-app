import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        dsoDemo: resolve(__dirname, 'demo/dso-visibility/index.html'),
        dsoDemoV2: resolve(__dirname, 'demo/dso-visibility-v2/index.html'),
      },
    },
  },
})
