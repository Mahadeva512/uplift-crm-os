import React, { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";

/**
 * Props:
 *  - open: boolean
 *  - onClose: fn
 *  - defaultText?: string
 *  - onInsert?: (text) => void
 *  - onSend?: (text) => Promise<void>
 *  - userEmail?: string            // CRM user's gmail (sender / mailbox owner)
 *  - threadId?: string             // Gmail threadId (for summarize)
 *  - subject?: string
 *  - lastMessages?: Array<{from: string, text?: string, snippet?: string}>
 *  - leadEmail?: string            // optional: helps suggest when no thread yet
 */
export default function CopilotModal({
  open,
  onClose,
  defaultText = "",
  onInsert,
  onSend,
  userEmail: userEmailProp,
  threadId,
  subject,
  lastMessages = [],
  leadEmail,
}) {
  const [tone, setTone] = useState("Neutral");
  const [summary, setSummary] = useState("Summary unavailable.");
  const [suggested, setSuggested] = useState(defaultText || "");
  const [loading, setLoading] = useState(false);

  // ----- API base + headers (fixed version) -----
  const ENV_BASE =
    (typeof window !== "undefined" && import.meta?.env?.VITE_API_BASE) || "";
  const LS_BASE = localStorage.getItem("API_BASE") || "";
  const API_BASE = (ENV_BASE || LS_BASE || "").trim();

  const join = (base, path) =>
    (base ? base.replace(/\/+$/, "") : "") + (path.startsWith("/") ? path : `/${path}`);

  const authHeader = useMemo(() => {
    const t =
      localStorage.getItem("uplift_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      "";
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  // ----- mailbox owner (sender) -----
  const userEmail = useMemo(() => {
    if (userEmailProp) return userEmailProp;
    try {
      const u = JSON.parse(localStorage.getItem("uplift_user") || "{}");
      if (u && u.email) return u.email;
    } catch (_) {}
    const ue = localStorage.getItem("user_email");
    if (ue && ue.includes("@")) return ue;
    return "";
  }, [userEmailProp]);

  // ----- token check -----
  const [checkingToken, setCheckingToken] = useState(false);
  const [hasToken, setHasToken] = useState(true);
  const [tokenErr, setTokenErr] = useState("");

  async function apiGet(path) {
    const url = API_BASE ? join(API_BASE, path) : path;
    const res = await fetch(url, { headers: { ...authHeader } });
    let data = null;
    try {
      data = await res.json();
    } catch {}
    if (!res.ok) {
      const err = { status: res.status, data };
      throw err;
    }
    return data;
  }

  async function apiPost(path, body) {
    const url = API_BASE ? join(API_BASE, path) : path;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = { status: res.status, data };
      throw err;
    }
    return data;
  }

  // ----- check token existence -----
  useEffect(() => {
    if (!open) return;
    if (!userEmail) {
      setHasToken(false);
      setTokenErr("No user email in session.");
      return;
    }
    setCheckingToken(true);
    setHasToken(true);
    setTokenErr("");
    apiGet(`/integrations/gmail/token/check?user_email=${encodeURIComponent(userEmail)}`)
      .then((d) => setHasToken(!!d?.exists))
      .catch((e) => {
        setHasToken(false);
        setTokenErr(e?.data?.detail || "Token check failed.");
      })
      .finally(() => setCheckingToken(false));
  }, [open, userEmail]);

  // ----- summarize -----
  async function handleSummarize() {
    if (!userEmail) return setSummary("Summary unavailable.");
    if (!threadId) return setSummary("Open a thread first to summarize.");
    if (!hasToken) return setSummary("Connect Gmail to enable summaries.");
    setLoading(true);
    try {
      const resp = await apiPost(`/ai/gmail/summarize`, {
        user_email: userEmail,
        thread_id: threadId,
        subject: subject || "(no subject)",
      });
      setSummary(resp?.summary || "Summary unavailable.");
    } catch (e) {
      const msg = e?.data?.detail || e?.data?.error || e?.message || "Summary unavailable.";
      setSummary(typeof msg === "string" ? msg : "Summary unavailable.");
    } finally {
      setLoading(false);
    }
  }

  // ----- suggest reply -----
  async function handleSuggest() {
    if (!hasToken) return setSuggested((s) => s || "");
    setLoading(true);
    try {
      const resp = await apiPost(`/ai/gmail/suggest`, {
        tone,
        subject: subject || "(no subject)",
        last_messages: lastMessages || [],
        lead_email: leadEmail || null,
      });
      setSuggested(resp?.reply || "");
    } catch (e) {
      const msg = e?.data?.detail || e?.message || "";
      setSuggested(
        msg ||
          `Thanks for your email about "${subject || "our discussion"}". Could you share a few suitable times for a quick call?`
      );
    } finally {
      setLoading(false);
    }
  }

  function connectUrl() {
    const url = `/integrations/gmail/auth?user_email=${encodeURIComponent(userEmail)}`;
    return API_BASE ? join(API_BASE, url) : url;
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-[min(980px,92vw)] max-h-[86vh] overflow-hidden rounded-2xl border border-white/10 bg-[#0A1224] shadow-2xl">
        {/* header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-yellow-400/20 text-yellow-300">
              ✨
            </span>
            <h3 className="text-lg font-semibold">AI Copilot – Smart Reply</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-white/10 active:scale-95 transition"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* token warning */}
        {!checkingToken && (!userEmail || !hasToken) && (
          <div className="mx-5 mt-4 rounded-lg border border-yellow-400/20 bg-yellow-400/10 px-3 py-2 text-[13px] text-yellow-200">
            {userEmail ? (
              <>
                No Gmail token found for <b>{userEmail}</b>. Please{" "}
                <a
                  href={connectUrl()}
                  target="_blank"
                  rel="noreferrer"
                  className="font-semibold underline"
                  title="Open Google OAuth in a new tab"
                >
                  Connect Gmail
                </a>{" "}
                and reopen this Copilot.
                {tokenErr ? <span className="ml-2 opacity-80">({tokenErr})</span> : null}
              </>
            ) : (
              "No user email in session. Please re-login."
            )}
          </div>
        )}

        {/* toolbar */}
        <div className="flex items-center gap-2 px-5 py-3">
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="rounded border border-white/10 bg-white/5 px-2 py-1 text-sm outline-none"
          >
            {["Neutral", "Friendly", "Formal", "Persuasive", "Empathetic", "Concise"].map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <button
            onClick={handleSummarize}
            disabled={loading || !threadId || !hasToken}
            className="rounded bg-white/10 px-3 py-1 text-sm hover:bg-white/20 disabled:opacity-50"
          >
            Summarize
          </button>
          <button
            onClick={handleSuggest}
            disabled={loading || !hasToken}
            className="rounded bg-yellow-400 px-3 py-1 text-sm font-semibold text-black hover:bg-yellow-300 disabled:opacity-50"
          >
            Suggest Reply
          </button>
          <div className="ml-auto text-xs text-gray-400">
            {checkingToken ? "Checking Gmail connection…" : ""}
          </div>
        </div>

        {/* body */}
        <div className="space-y-4 overflow-y-auto px-5 pb-5">
          {/* summary */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <p className="mb-1 text-xs text-gray-400">Summary</p>
            <div className="min-h-[100px] whitespace-pre-wrap text-sm text-gray-100">
              {loading ? "Thinking…" : summary}
            </div>
          </div>

          {/* suggested reply */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <p className="mb-1 text-xs text-gray-400">Suggested Reply</p>
            <textarea
              rows={8}
              value={suggested}
              onChange={(e) => setSuggested(e.target.value)}
              placeholder="Edit your reply..."
              className="h-[240px] w-full resize-none rounded-lg border border-white/10 bg-[#0C1428] p-3 text-sm text-gray-100 outline-none focus:border-yellow-400"
            />
          </div>
        </div>

        {/* footer */}
        <div className="flex items-center justify-end gap-2 border-t border-white/10 px-5 py-3">
          {onInsert && (
            <button
              onClick={() => onInsert(suggested || "")}
              disabled={!suggested}
              className="rounded bg-white/10 px-4 py-2 text-sm hover:bg-white/20 disabled:opacity-50"
            >
              Insert into Composer
            </button>
          )}
          {onSend && (
            <button
              onClick={async () => {
                if (!suggested) return;
                await onSend(suggested);
              }}
              disabled={!suggested}
              className="rounded bg-yellow-400 px-4 py-2 text-sm font-semibold text-black hover:bg-yellow-300 disabled:opacity-50"
            >
              ✈️ Send Now
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
