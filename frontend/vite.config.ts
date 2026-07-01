import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// REQ-1201: Vite-Konfiguration mit Proxy zu FastAPI
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Alle /api/, /ui/ und /docs Anfragen gehen an FastAPI
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ui": { target: "http://localhost:8000", changeOrigin: true },
      "/docs": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test-setup.ts",
  },
});
