// src/components/SignUpScreen.jsx
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { FiMail, FiLock, FiUser, FiBriefcase } from "react-icons/fi";

/**
 * ---------------------------------------------------------------------------
 * SignUpScreen.jsx (robust, production-ready)
 * - Manual signup → /auth/signup with company_name, full_name, email, password
 * - Google Sign-Up → redirects to backend /auth/google
 * - Consistent localStorage handling with LoginScreen (uplift_token, user_email)
 * ---------------------------------------------------------------------------
 */

export default function SignUpScreen({ onSwitch }) {
  const [formData, setFormData] = useState({
    company_name: "",
    full_name: "",
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [success, setSuccess] = useState("");

  // Best-effort base URL (env → same host → LAN fallback)
  const API_BASE_URL = useMemo(() => {
    const env = import.meta.env?.VITE_API_BASE_URL?.trim();
    if (env) return env.replace(/\/+$/, "");
    const host = window.location.hostname || "localhost";
    return `http://${host}:8000`;
  }, []);

  // ---- Helpers ----
  const handleInput = (field, value) =>
    setFormData((p) => ({ ...p, [field]: value }));

  // ---- Manual Signup ----
  async function handleSignup(e) {
    e.preventDefault();
    setErr("");
    setSuccess("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok)
        throw new Error(data.detail || data.message || "Signup failed");

      setSuccess("Account created successfully! You can now log in.");
      setTimeout(() => onSwitch?.("login"), 1500);
    } catch (error) {
      console.error("❌ Signup error:", error);
      setErr(
        error?.message || "Something went wrong while creating your account."
      );
    } finally {
      setLoading(false);
    }
  }

  // ---- Google Sign-Up ----
  function handleGoogleSignup() {
    const nextUrl =
      window.location.origin + (window.location.pathname || "/dashboard");
    const url = `${API_BASE_URL}/auth/google?next=${encodeURIComponent(nextUrl)}`;
    window.location.href = url;
  }

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
            Create Your Account
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Join Uplift CRM OS — Business Growth System
          </p>
        </div>

        <form onSubmit={handleSignup} className="space-y-5" noValidate>
          <div className="relative">
            <FiBriefcase className="absolute left-3 top-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Company Name"
              value={formData.company_name}
              onChange={(e) => handleInput("company_name", e.target.value)}
              className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-blue-600 outline-none"
              required
            />
          </div>

          <div className="relative">
            <FiUser className="absolute left-3 top-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Full Name"
              value={formData.full_name}
              onChange={(e) => handleInput("full_name", e.target.value)}
              className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-blue-600 outline-none"
              required
            />
          </div>

          <div className="relative">
            <FiMail className="absolute left-3 top-3.5 text-slate-500" />
            <input
              type="email"
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => handleInput("email", e.target.value)}
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
              value={formData.password}
              onChange={(e) => handleInput("password", e.target.value)}
              className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-blue-600 outline-none"
              autoComplete="new-password"
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
          {success && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-green-400 text-center text-sm"
              role="status"
            >
              {success}
            </motion.p>
          )}

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-yellow-400 to-yellow-300 hover:from-yellow-300 hover:to-yellow-200 text-slate-900 font-semibold shadow-lg shadow-yellow-900/40 transition-all disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Sign Up"}
          </motion.button>
        </form>

        <div className="flex items-center gap-2 mt-6">
          <div className="flex-1 h-px bg-slate-700" />
          <span className="text-slate-500 text-xs">or</span>
          <div className="flex-1 h-px bg-slate-700" />
        </div>

        {/* Google Sign-Up */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={handleGoogleSignup}
            className="flex items-center justify-center gap-3 w-full py-3 rounded-xl border border-slate-700 text-slate-200 hover:bg-slate-800 transition-all"
          >
            <img src="/google-icon.svg" alt="Google" className="w-5 h-5" />
            Continue with Google
          </button>
        </div>

        <p className="text-center text-slate-400 text-sm mt-4">
          Already have an account?{" "}
          <button
            type="button"
            onClick={() => onSwitch?.("login")}
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            Log In
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
