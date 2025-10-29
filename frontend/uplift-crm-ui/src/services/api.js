const API_BASE_URL =
  import.meta.env.VITE_API_URL || "https://uplift-crm-backend.onrender.com";

console.log("[API] Using base URL:", API_BASE_URL);

export default API_BASE_URL;
