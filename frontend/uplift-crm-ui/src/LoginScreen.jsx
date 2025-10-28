// src/components/LoginScreen.jsx
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { FiMail, FiLock } from "react-icons/fi";

/**
 * ---------------------------------------------------------------------------
 * LoginScreen.jsx (robust, production-ready)
 * - Email/password login → stores JWT, fetches user email, persists both
 * - Google Sign-In → redirects to backend, handles callback query & persists
 * - Always keeps localStorage in a consistent shape for MailPanel:
 *     - access token:  uplift_token / access_token
 *     - user email:    user_email
 *     - user name:     user_name  (best effort)
 * ---------------------------------------------------------------------------
 */

export default function LoginScreen({ onLogin, onSwitch }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // Best-effort base URL (env → same host → LAN fallback)
  const API_BASE_URL = useMemo(() => {
    const env = import.meta.env?.VITE_API_BASE_URL?.trim();
    if (env) return env.replace(/\/+$/, "");
    // If frontend is hosted next to backend with a proxy, you can also use "" (relative)
    // but for your current setup keep explicit http://host:8000 style:
    const host = window.location.hostname || "localhost";
    // if you run on a LAN IP (e.g., 192.168.x.x), keep the same IP:
    return `http://${host}:8000`;
  }, []);

  // --------- small helpers ----------

  const setAuth = ({ token, userEmail, userName, expiresInSec }) => {
    if (token) {
      localStorage.setItem("uplift_token", token);
      localStorage.setItem("access_token", token);
      localStorage.setItem("token", token); // backward compat
      if (expiresInSec) {
        const expAt = Date.now() + Number(expiresInSec) * 1000;
        localStorage.setItem("token_expires_at", String(expAt));
      }
    }
    if (userEmail) localStorage.setItem("user_email", userEmail);
    if (userName) localStorage.setItem("user_name", userName);
  };

  // Calls /auth/me (or /users/me) to read the email after we have a JWT
  const fetchAndPersistProfile = async (jwt) => {
    try {
      // Try the common ones in order:
      const endpoints = ["/auth/me", "/users/me", "/me"];
      let me = null;

      for (const ep of endpoints) {
        try {
          const res = await fetch(`${API_BASE_URL}${ep}`, {
            headers: { Authorization: `Bearer ${jwt}` },
          });
          if (res.ok) {
            me = await res.json();
            break;
          }
        } catch {
          /* try next */
        }
      }

      if (me) {
        const userEmail =
          me.email ||
          me.user?.email ||
          me.data?.email ||
          me.profile?.email ||
          null;

        const userName =
          me.full_name ||
          me.name ||
          me.user?.full_name ||
          me.user?.name ||
          null;

        if (userEmail) localStorage.setItem("user_email", userEmail);
        if (userName) localStorage.setItem("user_name", userName);
        return { userEmail, userName };
      }
    } catch {
      /* ignore */
    }
    return {};
  };

  // --------- handle email/password login ----------

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setErr("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Invalid credentials");

      const accessToken =
        data.access_token || data.token || data.jwt || data.accessToken;
      if (!accessToken) throw new Error("Token not returned by server");

      setAuth({
        token: accessToken,
        expiresInSec: data.expires_in || data.expiresIn,
      });

      // fetch user profile/email and persist (so MailPanel has it)
      const { userEmail } = await fetchAndPersistProfile(accessToken);

      // If we still don’t have user_email, use the typed email as a fallback
      if (!localStorage.getItem("user_email")) {
        if (userEmail) localStorage.setItem("user_email", userEmail);
        else if (email) localStorage.setItem("user_email", email);
      }

      onLogin?.(accessToken);
    } catch (error) {
      console.error("❌ Login error:", error);
      setErr(
        error?.message ||
          "Sign-in failed. Please check your email and password."
      );
    } finally {
      setLoading(false);
    }
  }

  // --------- Google Sign-In ----------

  function handleGoogleLogin() {
    /**
     * Your backend’s /auth/google will do:
     *  - redirect to Google
     *  - on success, /auth/google/callback persists the Google token file
     *  - then redirects back to frontend (we'll read ?connected=<email> or ?email=)
     *
     * Optionally you can support `next=` on the backend; if not present,
     * simple redirect to /auth/google is fine.
     */
    const nextUrl =
      window.location.origin + (window.location.pathname || "/dashboard");
    const url = `${API_BASE_URL}/auth/google?next=${encodeURIComponent(nextUrl)}`;
    window.location.href = url;
  }

  // --------- Handle OAuth callback query and/or recover session ----------

  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const qp = url.searchParams;

      // 1) If backend appended the connected email as ?connected=<email> or ?email=...
      const connectedEmail =
        qp.get("connected") || qp.get("email") || qp.get("user_email");
      if (connectedEmail) {
        localStorage.setItem("user_email", connectedEmail);
        // Clean the URL
        qp.delete("connected");
        qp.delete("email");
        qp.delete("user_email");
        window.history.replaceState({}, "", url.pathname + url.search);
      }

      // 2) If backend also sent a token in the URL (rare), persist it:
      const tokenFromUrl =
        qp.get("access_token") || qp.get("token") || qp.get("jwt");
      if (tokenFromUrl) {
        setAuth({ token: tokenFromUrl });
        qp.delete("access_token");
        qp.delete("token");
        qp.delete("jwt");
        window.history.replaceState({}, "", url.pathname + url.search);
      }

      // 3) If we already have a token but *no* user_email, fetch profile once.
      const existingToken =
        localStorage.getItem("uplift_token") ||
        localStorage.getItem("access_token") ||
        localStorage.getItem("token");

      if (existingToken && !localStorage.getItem("user_email")) {
        fetchAndPersistProfile(existingToken);
      }
    } catch {
      /* safe no-op */
    }
  }, [API_BASE_URL]);

  // UI
  return (
    <div className="relative flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(0,72,232,0.35),transparent_40%),radial-gradient(circle_at_80%_80%,rgba(250,204,21,0.25),transparent_40%)] animate-pulse-slow" />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 w-full max-w-md mx-4 my-10 glass-card p-10"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-white tracking-wide drop-shadow-lg">
            Uplift CRM OS
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Business Growth Operating System
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5" noValidate>
          <div className="relative">
            <FiMail className="absolute left-3 top-3.5 text-slate-500" />
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-blue-600 outline-none"
              autoComplete="email"
              required
            />
          </div>

          <div className="relative">
            <FiLock className="absolute left-3 top-3.5 text-slate-500" />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-blue-600 outline-none"
              autoComplete="current-password"
              required
              minLength={6}
            />
          </div>

          {err && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-red-400 text-center text-sm"
              role="alert"
            >
              {err}
            </motion.p>
          )}

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold shadow-lg shadow-blue-900/40 transition-all disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign In"}
          </motion.button>
        </form>

        <div className="flex items-center gap-2 mt-6">
          <div className="flex-1 h-px bg-slate-700" />
          <span className="text-slate-500 text-xs">or</span>
          <div className="flex-1 h-px bg-slate-700" />
        </div>

        {/* Google Sign-In */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="flex items-center justify-center gap-3 w-full py-3 rounded-xl border border-slate-700 text-slate-200 hover:bg-slate-800 transition-all"
          >
            <img src="/google-icon.svg" alt="Google" className="w-5 h-5" />
            Continue with Google
          </button>
        </div>

        <p className="text-center text-slate-400 text-sm mt-4">
          Don’t have an account?{" "}
          <button
            type="button"
            onClick={() => onSwitch?.("signup")}
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            Sign Up
          </button>
        </p>

        <p className="text-center text-slate-500 text-xs mt-8">
          © {new Date().getFullYear()} Uplift Business Growth Solutions. All
          rights reserved.
        </p>
      </motion.div>
    </div>
  );
}
