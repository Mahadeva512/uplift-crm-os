// src/services/api.js
import axios from "axios";

/**
 * Single source of truth for backend base URL.
 * Uses only VITE_API_URL from your frontend .env (no localhost fallbacks).
 */
const API_BASE_URL = import.meta.env.VITE_API_URL;

if (!API_BASE_URL) {
  console.error("❌ Missing VITE_API_URL in frontend .env. Set it to your Render backend URL.");
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token if present
api.interceptors.request.use((config) => {
  const raw =
    localStorage.getItem("uplift_token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token");
  if (raw) {
    const token = raw.replace(/^\"|\"$/g, "");
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const base = API_BASE_URL || "(unset)";
    console.warn("[API ERROR]", {
      base,
      url: error?.config?.url,
      status: error?.response?.status,
      data: error?.response?.data,
      message: error?.message,
    });
    return Promise.reject(error);
  }
);

export { API_BASE_URL };
export default api;
