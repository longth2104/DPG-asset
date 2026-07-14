import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  // The app itself has a top-level route at /assets (the asset registry) —
  // Vite's default build output directory is also named "assets", which
  // would collide with nginx's static-cache location block. Rename it.
  build: { assetsDir: 'static' },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
