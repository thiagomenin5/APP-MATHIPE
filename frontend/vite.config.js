import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Base para que los assets se resuelvan en producción en /assets/mathipe_ui/spa/
const base = "/assets/mathipe_ui/spa/";

export default defineConfig({
  plugins: [vue()],
  base,
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    outDir: "../mathipe_ui/public/spa",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API y assets al backend ERPNext (evita CORS en desarrollo)
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/assets": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/files": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
