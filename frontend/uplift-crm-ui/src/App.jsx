// App.jsx — Uplift CRM OS Core Navigation
import { useState, useEffect } from "react";
import LoginScreen from "./LoginScreen";
import SignUpScreen from "./SignUpScreen";
import Dashboard from "./Dashboard";
import Leads from "./Leads";
import ActivityCenter from "./pages/ActivityCenter"; // ✅ AI-powered Activity Center

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("uplift_token"));
  const [screen, setScreen] = useState("login");

  // ✅ Auto-login check
  useEffect(() => {
    const savedToken = localStorage.getItem("uplift_token");
    if (savedToken) {
      setToken(savedToken);
      setScreen("dashboard");
    }
  }, []);

// ✅ Handle Google Sign-In redirect (detect ?google_token= in URL)
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const googleToken = urlParams.get("google_token");
  const email = urlParams.get("email");

  if (googleToken) {
    console.log("✅ Google sign-in detected:", email);
    localStorage.setItem("uplift_token", googleToken);
    setToken(googleToken);
    setScreen("dashboard");

    // 🧠 Immediately fetch the user’s company profile
    (async () => {
      try {
        const API_BASE =
          import.meta.env?.VITE_API_BASE_URL?.trim() ||
          `http://${window.location.hostname}:8000`;

        const res = await fetch(`${API_BASE}/company/profile`, {
          headers: { Authorization: `Bearer ${googleToken}` },
        });

        if (res.ok) {
          const company = await res.json();
          localStorage.setItem("uplift_company", JSON.stringify(company));

          // Create a minimal user object (until /me endpoint added)
          localStorage.setItem(
            "uplift_user",
            JSON.stringify({
              email,
              full_name: email?.split("@")[0] || "",
            })
          );

          console.log("🏢 Company data synced:", company.company_name);
        } else {
          console.warn("⚠️ Could not fetch company profile:", res.status);
        }
      } catch (err) {
        console.error("❌ Failed to load company info:", err);
      }
    })();

    // 🧹 Clean up URL so query params disappear after login
    window.history.replaceState({}, document.title, "/");
  }
}, []);

  const handleLogin = (t) => {
    localStorage.setItem("uplift_token", t);
    setToken(t);
    setScreen("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("uplift_token");
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

  // 🔹 Activity Center (AI Copilot already globally available)
  if (screen === "activity-center")
    return <ActivityCenter onBack={() => setScreen("dashboard")} />;

  // 🔹 Default fallback
  return <Dashboard onLogout={handleLogout} onSwitch={setScreen} />;
}
