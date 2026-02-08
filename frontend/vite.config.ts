import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths';

// https://vitejs.dev/config/
export default defineConfig({
  base: "/",

  plugins: [
    tsconfigPaths(), 
    react()
  ],
  preview: {
    port: 8030,
    strictPort: true,
  },
  server: {
    port: 8030,
    strictPort: true,
    host: true,
    origin: "http://0.0.0.0:8030",
  }
})
