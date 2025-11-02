// src/api/apiClient.js
import axios from "axios";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL && import.meta.env.VITE_API_BASE_URL.trim().replace(/\/+$/, "")) ||
  "https://uplift-crm-backend.onrender.com";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

let getAuthEmail = null;
try {
  if (typeof window !== "undefined" && window.__upliftGetUserEmail__) {
    getAuthEmail = window.__upliftGetUserEmail__;
  }
} catch {}

apiClient.interceptors.request.use((config) => {
  try {
    let userEmail = null;
    if (getAuthEmail) userEmail = getAuthEmail();
    if (!userEmail && typeof localStorage !== "undefined") {
      userEmail =
        localStorage.getItem("uplift_user_email") ||
        localStorage.getItem("user_email") ||
        null;
    }
    let token = null;
    if (typeof localStorage !== "undefined") {
      if (userEmail) {
        token = localStorage.getItem(`token_${userEmail}`);
      }
      if (!token) {
        token =
          localStorage.getItem("uplift_token") ||
          localStorage.getItem("token") ||
          null;
      }
    }
    if (token) {
      config.headers = config.headers || {};
      if (!config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    if (userEmail) {
      config.headers = config.headers || {};
      if (!config.headers["X-User-Email"]) {
        config.headers["X-User-Email"] = userEmail;
      }
    }
  } catch (err) {
    console.warn("apiClient interceptor error:", err);
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    if (status === 401 || status === 403) {
      console.warn("Auth error", status);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
export { API_BASE_URL };
