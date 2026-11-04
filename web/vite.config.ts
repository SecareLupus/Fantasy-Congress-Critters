import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs separately (`critters serve`); Vite forwards /api to it.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
