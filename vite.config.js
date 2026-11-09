// Vite builds the Vue components and the viewer into static/dist/ (functional
// design 10.2). Flask renders the pages and loads the entries below: from the
// dev server during development, via static/dist/.vite/manifest.json when built.
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === "build" ? "/static/dist/" : "/",
  publicDir: false,
  build: {
    outDir: "static/dist",
    emptyOutDir: true,
    manifest: true,
    // Third-party licences (Codex: GPL-2.0-or-later, Vue: MIT) next to the bundle (FO 12.1).
    license: true,
    rollupOptions: {
      input: {
        base: "frontend/main-base.js",
        index: "frontend/main-index.js",
        objecten: "frontend/main-objecten.js",
        commons: "frontend/main-commons.js",
        verbruik: "frontend/main-verbruik.js",
        changelog: "frontend/main-changelog.js",
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
    cors: true,
  },
  test: {
    environment: "jsdom",
    include: ["frontend/**/*.test.js"],
  },
}));
