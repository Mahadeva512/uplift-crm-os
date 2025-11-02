// App.jsx — Uplift CRM OS Core Navigation (Enhanced)
import { useState, useEffect } from "react";
import LoginScreen from "./LoginScreen";
import SignUpScreen from "./SignUpScreen";
import Dashboard from "./Dashboard";
import Leads from "./Leads";
import ActivityCenter from "./pages/ActivityCenter"; // ✅ AI-powered Activity Center

const API_BASE =
  (import.meta.env?.VITE_API_BASE_URL?.trim() ||
    import.meta.env?.VITE_API_URL?.trim() ||
    "https://uplift-crm-backend.onrender.com").replace(/\/+$/, "");

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("uplift_token"));
  const [screen, setScreen] = useState("login");
  const [loading, setLoading] = useState(false);

  // ✅ Auto-login check (from localStorage)
  useEffect(() => {
    const savedToken = localStorage.getItem("uplift_token");
    if (savedToken) {
      setToken(savedToken);
      setScreen("dashboard");
    }
  }, []);

  // ✅ Handle Google / OAuth redirects
  useEffect(() => {
    const qp = new URLSearchParams(window.location.search);
    const googleToken = qp.get("google_token");
    const tokenParam = qp.get("token");
    const code = qp.get("code");
    const email = qp.get("email");

    async function finalizeAuth(jwt) {
      try {
        if (!jwt) return;
        localStorage.setItem("uplift_token", jwt);
        setToken(jwt);
        setScreen("dashboard");

        // ✅ Verify session and sync profile
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${jwt}` },
          credentials: "include",
        });
        if (res.ok) {
          const user = await res.json();
          localStorage.setItem("uplift_user", JSON.stringify(user));
        }

        // ✅ Fetch company profile
        const resCompany = await fetch(`${API_BASE}/company/profile`, {
          headers: { Authorization: `Bearer ${jwt}` },
        });
        if (resCompany.ok) {
          const company = await resCompany.json();
          localStorage.setItem("uplift_company", JSON.stringify(company));
          console.log("🏢 Company data synced:", company.company_name);
        }

        // ✅ Clean URL
        window.history.replaceState({}, document.title, "/");
      } catch (err) {
        console.error("❌ Auth finalize error:", err);
      }
    }

    // ✅ Handle direct token param
    if (googleToken || tokenParam) {
      finalizeAuth(googleToken || tokenParam);
      return;
    }

    // ✅ Handle Google OAuth Code Flow
    async function exchangeCodeForToken() {
      try {
        setLoading(true);
        const redirect_uri = window.location.origin;
        const url = new URL(`${API_BASE}/auth/google/callback`);
        url.searchParams.set("code", code);
        url.searchParams.set("redirect_uri", redirect_uri);

        const res = await fetch(url.toString(), {
          method: "GET",
          credentials: "include",
        });

        if (!res.ok) {
          console.error("Google code exchange failed:", res.status);
          return;
        }

        const data = await res.json();
        const jwt = data?.token || data?.access_token;
        if (jwt) {
          await finalizeAuth(jwt);
        } else {
          console.error("⚠️ No token in Google callback response:", data);
        }
      } catch (err) {
        console.error("❌ Error exchanging Google code:", err);
      } finally {
        setLoading(false);
      }
    }

    if (code) {
      exchangeCodeForToken();
      return;
    }
  }, []);

  // ✅ Manual login via form (passed from LoginScreen)
  const handleLogin = (t) => {
    localStorage.setItem("uplift_token", t);
    setToken(t);
    setScreen("dashboard");
  };

  // ✅ Logout
  const handleLogout = () => {
    localStorage.removeItem("uplift_token");
    localStorage.removeItem("uplift_company");
    localStorage.removeItem("uplift_user");
    setToken(null);
    setScreen("login");
  };

  // 🔹 Login / Signup Flow
  if (!token) {
    return screen === "login" ? (
      <LoginScreen onLogin={handleLogin} onSwitch={setScreen} />
    ) : (
      <SignUpScreen onSwitch={setScreen} onLogin={handleLogin} />
    );
  }

  // 🔹 After Login
  if (screen === "dashboard")
    return <Dashboard onLogout={handleLogout} onSwitch={setScreen} />;

  if (screen === "leads")
    return <Leads onBack={() => setScreen("dashboard")} token={token} />;

  // 🔹 Activity Center (AI Copilot globally available)
  if (screen === "activity-center")
    return <ActivityCenter onBack={() => setScreen("dashboard")} />;

  // 🔹 Default fallback
  return <Dashboard onLogout={handleLogout} onSwitch={setScreen} />;
}
