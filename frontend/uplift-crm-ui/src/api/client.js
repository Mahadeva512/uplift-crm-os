// src/api/client.js
import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://uplift-crm-os.onrender.com";

console.log("✅ Using API base:", API_BASE_URL);

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ Automatically attach bearer token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("uplift_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default client;
