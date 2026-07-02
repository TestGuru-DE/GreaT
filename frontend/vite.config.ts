import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// REQ-1201: Vite-Konfiguration mit Proxy zu FastAPI
// REQ-4007: GREAT_PORT Umgebungsvariable unterstützen
const backendPort = process.env.GREAT_PORT || "8000";
const backendUrl = `http://localhost:${backendPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Alle /api/, /ui/ und /docs Anfragen gehen an FastAPI
      "/api": { target: backendUrl, changeOrigin: true },
      "/ui": { target: backendUrl, changeOrigin: true },
      "/docs": { target: backendUrl, changeOrigin: true },
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
