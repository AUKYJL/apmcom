import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// В разработке всё, что относится к Django (API, админка, загруженные файлы),
// проксируется на бэкенд, поэтому cookie сессии и CSRF работают на одном домене.
const backend = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': backend,
      '/admin': backend,
      '/media': backend,
      '/static': backend,
    },
  },
})
