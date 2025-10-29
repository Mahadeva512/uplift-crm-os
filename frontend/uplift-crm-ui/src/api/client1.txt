// src/api/client.js
import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://192.168.29.70:8000",
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

// ✅ Attach token from localStorage to every request
client.interceptors.request.use(
  (config) => {
    // Try all possible keys (login or signup may use different ones)
    const raw =
      localStorage.getItem("uplift_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token");

    if (raw) {
      // strip accidental quotes if JSON-stringified
      const token = raw.replace(/^"|"$/g, "");
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.warn("⚠️ No token found in localStorage.");
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default client;
