// src/components/MailPanel.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  ArrowLeft, Send, RefreshCw, Paperclip,
  MailOpen, Mail, Search, Download
} from "lucide-react";
import CopilotModal from "./CopilotModal";

/* ======================================
   Helpers & Config
====================================== */
// ✅ Use only VITE_API_URL (no localhost fallback)
const API_BASE = import.meta.env.VITE_API_URL;
const AUTO_REFRESH_MS = 120000;
const DRAFT_KEY = (leadId) => `uplift.mail.draft.${leadId || "unknown"}`;

function b64urlDecode(s) {
  try {
    const pad = (str) => str + "===".slice((str.length + 3) % 4);
    return decodeURIComponent(
      atob(pad(s.replace(/-/g, "+").replace(/_/g, "/")))
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
  } catch {
    return s;
  }
}

export default function MailPanel({ lead, onBack }) {
  const userEmail = (lead?.user_email || "").trim();
  const leadEmail = (lead?.email || "").trim();
  const leadId = lead?.lead_id || lead?.uid || "";

  const axiosClient = useMemo(
    () =>
      axios.create({
        baseURL: API_BASE,
        headers: userEmail ? { "X-User-Email": userEmail } : {},
      }),
    [userEmail]
  );

  const refreshTimer = useRef(null);
  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState(localStorage.getItem(DRAFT_KEY(leadId)) || "");

  // ---------------- Load ----------------
  async function loadMessages() {
    if (!userEmail || !leadEmail) return;
    setLoading(true);
    try {
      const { data } = await axiosClient.get(`/integrations/gmail/threads`, {
        params: { lead_email: leadEmail },
      });
      setThreads(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Mail load failed:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMessages();
    if (refreshTimer.current) clearInterval(refreshTimer.current);
    refreshTimer.current = setInterval(loadMessages, AUTO_REFRESH_MS);
    return () => clearInterval(refreshTimer.current);
  }, [userEmail, leadEmail]);

  // ---------------- Actions ----------------
  async function sendMail() {
    if (!draft.trim()) return;
    try {
      await axiosClient.post(`/integrations/gmail/send`, {
        to: leadEmail,
        subject: `Re: ${activeThread?.subject || "Message from Uplift"}`,
        body: draft,
        threadId: activeThread?.id || null,
      });
      setDraft("");
      localStorage.removeItem(DRAFT_KEY(leadId));
      await loadMessages();
    } catch (e) {
      console.error("Send email failed:", e);
      alert("Failed to send email.");
    }
  }

  async function markThread(threadId, action) {
    try {
      await axiosClient.post(`/integrations/gmail/thread/mark`, {
        threadId,
        action, // "read" | "unread" | "star" | "unstar"
      });
      await loadMessages();
    } catch (e) {
      console.error("Mark thread failed:", e);
    }
  }

  // Save draft locally
  useEffect(() => {
    localStorage.setItem(DRAFT_KEY(leadId), draft || "");
  }, [draft, leadId]);

  // --- UI kept as-is (compose box, list, etc.) ---
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-3 p-2 border-b border-white/10">
        <button onClick={onBack} className="text-slate-300 hover:text-white"><ArrowLeft size={18} /></button>
        <div className="text-white/90 text-sm">Mail • {leadEmail || "No email"}</div>
        <div className="ml-auto">
          <button onClick={loadMessages} className="text-slate-300 hover:text-white"><RefreshCw size={16} /></button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3">
        {threads.length === 0 ? (
          <div className="text-slate-400 text-sm">No emails yet.</div>
        ) : (
          <ul className="space-y-2">
            {threads.map((t) => (
              <li key={t.id} className="p-2 rounded-lg bg-white/5">
                <div className="text-white text-sm">{t.subject || "(no subject)"}</div>
                <div className="text-slate-400 text-xs">{t.snippet || ""}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t border-white/10 p-2">
        <textarea
          rows={3}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full bg-[#0E1630] text-white px-3 py-2 rounded"
          placeholder="Write your email…"
        />
        <div className="flex justify-end pt-2">
          <button onClick={sendMail} className="px-3 py-2 bg-[#00BFFF] text-[#0B1222] rounded-lg hover:opacity-90 flex items-center gap-2">
            <Send size={16} /> Send
          </button>
        </div>
      </div>
    </div>
  );
}
