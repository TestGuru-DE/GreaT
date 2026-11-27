import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";

// REQ-1201: Vite-Konfiguration mit Proxy zu FastAPI
// REQ-4007: GREAT_PORT Umgebungsvariable unterstützen
const backendPort = process.env.GREAT_PORT || "8000";
const backendUrl = `http://localhost:${backendPort}`;

// BUG R-04/A-14: Version fuer die Oberflaeche aus package.json (statt fest im Text)
const appVersion: string = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf-8")).version;

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  server: {
    port: 5173,
    proxy: {
      // Alle /api/, /ui/, /docs und /auth Anfragen gehen an FastAPI
      "/api": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/ui": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/docs": {
        target: backendUrl,
        changeOrigin: true,
      },
      // REQ-4001: Auth-Endpunkte (JWT in httpOnly-Cookies)
      "/auth": {
        target: backendUrl,
        changeOrigin: true,
      },
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
    exclude: ['node_modules', 'dist', 'e2e'],
  },
});
