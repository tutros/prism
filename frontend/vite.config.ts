import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // Never inline assets as data: URIs. The production nginx CSP is
    // `font-src 'self'`, which blocks data: fonts; small font subsets
    // (e.g. cyrillic-ext) fall under Vite's default 4 KB inline limit.
    // scripts/check-dist.mjs enforces this after every build.
    assetsInlineLimit: 0,
  },
})
