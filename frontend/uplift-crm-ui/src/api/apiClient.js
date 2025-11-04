// src/api/apiClient.js
import axios from "axios";

// ✅ Set the correct backend base URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://uplift-crm-os.onrender.com";

// ✅ Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ Attach token if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("uplift_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ✅ Optional user email handling (used by Gmail sync, AI, etc.)
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
