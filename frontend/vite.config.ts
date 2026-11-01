import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The API is served from the same origin under /api (ADR-011). In development Vite forwards
// /api to the FastAPI server started with `make run` in backend/.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
