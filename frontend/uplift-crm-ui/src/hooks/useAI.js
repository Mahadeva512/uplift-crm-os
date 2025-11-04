// src/hooks/useAI.js
// Unified AI bridge for /ai/* endpoints (summarize, next-step, insights, weekly-report)
// 100% safe across Vite / CRA / Next / PWA builds.
// 🔒 Hardened for local + cloud + mobile (Android PWA) environments.

function resolveApiBase() {
  try {
    if (typeof import.meta !== "undefined" && import.meta?.env?.VITE_API_BASE_URL) {
      return import.meta.env.VITE_API_BASE_URL;
    }
  } catch (_) {}

  try {
    if (typeof process !== "undefined" && process?.env) {
      return (
        process.env.VITE_API_BASE_URL ||
        process.env.REACT_APP_API_BASE ||
        process.env.NEXT_PUBLIC_API_BASE ||
        process.env.API_BASE
      );
    }
  } catch (_) {}

  try {
    if (typeof window !== "undefined") {
      // Fallback from window or localStorage (set once when app boots)
      return window.__API_BASE__ || localStorage.getItem("API_BASE");
    }
  } catch (_) {}

  return "https://uplift-crm-os.onrender.com"; // final fallback
}

// ✅ 1. Initialize and persist API base globally
// 🔥 Guaranteed runtime fallback
let API_BASE = resolveApiBase();
if (!API_BASE || API_BASE === "null" || API_BASE === "undefined") {
  API_BASE = "https://uplift-crm-os.onrender.com";
}
if (typeof window !== "undefined") {
  window.__API_BASE__ = API_BASE;
  localStorage.setItem("API_BASE", API_BASE);
}
console.log("✅ API_BASE set to:", API_BASE);


// ✅ 2. Use correct auth token
const getToken = () =>
  (typeof localStorage !== "undefined" &&
    (localStorage.getItem("uplift_token") ||
      localStorage.getItem("token"))) ||
  "";

// ✅ 3. Core AI fetch wrapper (Render-safe + URL clean + timeout + token)
async function aiFetch(
  path,
  { method = "GET", body, headers = {}, timeout = 20000 } = {}
) {
  const API_BASE =
    (import.meta.env.VITE_API_BASE_URL_URL &&
      import.meta.env.VITE_API_BASE_URL_URL.trim().replace(/\/+$/, "")) ||
    "https://uplift-crm-os.onrender.com";

  // ensure path starts with '/'
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  const h = new Headers(headers);
  if (body && !(body instanceof FormData) && !h.has("Content-Type")) {
    h.set("Content-Type", "application/json");
  }

  const token = getToken?.();
  if (token && !h.has("Authorization")) {
    h.set("Authorization", `Bearer ${token}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(`${API_BASE}${cleanPath}`, {
      method,
      body:
        body && !(body instanceof FormData) ? JSON.stringify(body) : body,
      headers: h,
      signal: controller.signal,
      credentials: "include",
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.error("❌ AI Request Failed", cleanPath, res.status, text);
      throw new Error(`${res.status} ${res.statusText} — ${text}`);
    }

    return await res.json().catch(() => ({}));
  } catch (err) {
    clearTimeout(timeoutId);
    console.error("⚠️ AI fetch error:", err.message || err);
    throw err;
  }
}

// ✅ 4. Unified exportable hook
export function useAI() {
  // Insights overview
  const getInsights = (params = { days: 7, user_id: "", lead_id: "" }) => {
    const qs = new URLSearchParams();
    if (params.days) qs.set("days", String(params.days));
    if (params.user_id) qs.set("user_id", params.user_id);
    if (params.lead_id) qs.set("lead_id", params.lead_id);
    return aiFetch(`/ai/ai/insights?${qs.toString()}`);
  };

  // Weekly AI report
  const getWeeklyReport = () => aiFetch(`/ai/ai/insights?days=7`);

  // Activity-based AI
  const summarizeActivity = (activityId) =>
    aiFetch(`/ai/ai/summarize/${activityId}`, { method: "POST" });

  const suggestNextStep = (activityId) =>
    aiFetch(`/ai/ai/next-step/${activityId}`, { method: "POST" });

  // Optional: health check ping
  const ping = () => aiFetch(`/`);

  return {
    API_BASE,
    getInsights,
    getWeeklyReport,
    summarizeActivity,
    suggestNextStep,
    ping,
  };
}
