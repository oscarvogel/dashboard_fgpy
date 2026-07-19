import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      input: 'index.html',
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router'],
          'charts': ['apexcharts', 'vue3-apexcharts'],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    fs: {
      // Allow both drive letters in case the workspace is mounted/mapped.
      strict: false,
      allow: [
        'O:/django/fgpy/frontend',
        'V:/django/fgpy/frontend',
      ],
    },
    watch: {
      // Mapped/network drives on Windows can fail with fs.watch (UNKNOWN: watch).
      // Polling keeps HMR stable when the project is on drive O:.
      usePolling: true,
      interval: 1000,
    },
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
