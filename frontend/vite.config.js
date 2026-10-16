import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In local dev (`npm run dev`) the API is proxied to a backend on :8000, so the
// browser always calls same-origin `/api/...` exactly as it does behind Nginx
// and the Kubernetes Ingress.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
