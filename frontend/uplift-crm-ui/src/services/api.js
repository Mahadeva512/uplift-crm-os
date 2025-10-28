// src/services/api.js
import axios from "axios";

/**
 * Robust API base resolution
 * Priority:
 *   1) localStorage.API_BASE (manual override)
 *   2) import.meta.env.VITE_API_BASE_URL (from .env)
 *   3) Same host as the app but port 8000 (works when FE & BE on same machine/IP)
 *   4) LAN fallbacks you use often (edit to your network)
 *
 * You can override at runtime in DevTools:
 *   localStorage.setItem('API_BASE', 'http://192.168.29.70:8000')
 *   location.reload()
 */
function resolveApiBase() {
  // 1) Manual runtime override
  const ls = (key) => {
    try {
      return localStorage.getItem(key) || "";
    } catch {
      return "";
    }
  };
  const manual = ls("API_BASE");
  if (manual) return manual;

  // 2) .env (Vite)
  const envBase = import.meta?.env?.VITE_API_BASE_URL;
  if (envBase) return envBase;

  // 3) Same host as app, port 8000 (best default)
  const host = window.location.hostname;
  const sameHostBase = `http://${host}:8000`;

  // 4) Known LAN fallbacks (customize these for your setup)
  const lanCandidates = [
    "http://192.168.29.70:8000",
    "http://10.70.190.116:8000",
    "http://127.0.0.1:8000",
  ];

  // Prefer same-host first, then known LANs
  const candidates = [sameHostBase, ...lanCandidates];

  // Pick the first one — if you need to change at runtime, use localStorage.API_BASE
  return candidates[0];
}

let API_BASE_URL = resolveApiBase();

// Expose for quick debugging
window.__API_BASE__ = API_BASE_URL;
console.info("[API] Using base:", API_BASE_URL);

/**
 * Axios instance
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/**
 * Attach auth token, if any
 */
api.interceptors.request.use(
  (config) => {
    const token =
      localStorage.getItem("uplift_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Optional: soft guidance when we see cross-host confusion
 * (Helps you catch when FE points at 127.0.0.1 but BE is on 192.168.*)
 */
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error?.config?.baseURL || "";
    const appHost = window.location.hostname;
    const looksLikeMismatch =
      appHost !== "127.0.0.1" &&
      appHost !== "localhost" &&
      url.includes("127.0.0.1");

    if (looksLikeMismatch) {
      console.warn(
        "[API] Base URL appears to be 127.0.0.1 while app is served from",
        appHost,
        "→ Set a correct base with:",
        `localStorage.setItem('API_BASE', 'http://${appHost}:8000'); location.reload();`
      );
    }
    return Promise.reject(error);
  }
);

export default api;
