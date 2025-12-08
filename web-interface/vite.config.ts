import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': './src'
    }
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_HOST || 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: (process.env.VUE_APP_API_HOST || 'http://localhost:8000').replace(/^http:\/\//, 'ws://'),
        ws: true
      }
    }
  }
})
