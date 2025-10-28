import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ---------------------------------------------------------------------------
// ✅ Uplift CRM OS — Vite Configuration
// ---------------------------------------------------------------------------
// This configuration ensures the app runs smoothly on desktop, mobile, and LAN.
// It allows access from any device on the same Wi-Fi network (important for testing).
// ---------------------------------------------------------------------------

export default defineConfig({
  plugins: [react()],

  // -------------------------------------------------------------------------
  // ✅ Development Server Settings
  // -------------------------------------------------------------------------
  server: {
    host: true,        // exposes the dev server to LAN (mobile access)
    port: 5173,        // consistent port for frontend
    strictPort: true,  // if 5173 is busy, throw error instead of random port
    open: false,       // don't auto-open browser
    cors: true,        // allow all origins in dev mode (for FastAPI calls)
  },

  // -------------------------------------------------------------------------
  // ✅ Build Optimization (for future production builds)
  // -------------------------------------------------------------------------
  build: {
    outDir: 'dist',           // output folder
    sourcemap: true,          // enables debugging in production builds
    chunkSizeWarningLimit: 1000, // silence large chunk warnings
  },

  // -------------------------------------------------------------------------
  // ✅ Resolve Settings
  // -------------------------------------------------------------------------
  resolve: {
    alias: {
      '@': '/src', // shorthand import (e.g., import X from '@/components/X')
    },
  },
});
