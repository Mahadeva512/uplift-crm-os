// src/components/LeadCard.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Phone, MessageSquare, Mail, ClipboardList } from "lucide-react";
import MailPanel from "./MailPanel";
import { createActivity } from "@/api/activities";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/services/api";

/**
 * Gmail availability cache (shared across cards)
 */
let gmailAvailable = "unknown";
let gmailCheckedAt = 0;
const GMAIL_CHECK_TTL_MS = 5 * 60 * 1000; // 5 min

async function checkGmailAvailability(userEmail) {
  const now = Date.now();
  if (gmailAvailable !== "unknown" && now - gmailCheckedAt < GMAIL_CHECK_TTL_MS)
    return gmailAvailable;

  try {
    await api.get("/integrations/gmail/status", {
      headers: userEmail ? { "X-User-Email": userEmail } : undefined,
      params: userEmail ? { user_email: userEmail } : undefined,
    });
    gmailAvailable = true;
  } catch (err) {
    const code = err?.response?.status;
    gmailAvailable = !(code === 401 || code === 403 || code === 404);
  } finally {
    gmailCheckedAt = now;
  }
  return gmailAvailable;
}

const userCache = {};

export default function LeadCard({ lead = {}, onView, onActivity }) {
  const [unread, setUnread] = useState(0);
  const [loadingUnread, setLoadingUnread] = useState(false);
  const [showMail, setShowMail] = useState(false);
  const [creatorName, setCreatorName] = useState(null);
  const [gmailOn, setGmailOn] = useState(gmailAvailable === true);
  const muted404Ref = useRef(false);
  const pollTimerRef = useRef(null);
  const { user } = useAuthStore?.() || { user: {} };

  const signedInEmail = useMemo(
    () =>
      user?.email ||
      localStorage.getItem("user_email") ||
      localStorage.getItem("email") ||
      undefined,
    [user?.email]
  );

  // ---------------------- ACTIVITY LOG ----------------------
  const logActivity = async (type, desc, extraMeta = {}) => {
    if (!lead?.id || !type) return;
    try {
      const payload = {
        lead_id: lead.id,
        type,
        title: `${type} — ${lead.business_name || "Lead"}`,
        description: desc,
        status: "Completed",
        outcome: "Pending Notes",
        assigned_to: user?.id,
        source_channel: "LeadCard",
        meta: { auto_logged: true, ...extraMeta },
      };
      await createActivity(payload);
    } catch (err) {
      console.error("Activity log failed:", err);
    }
  };

  // ---------------------- FETCH UNREAD ----------------------
  const fetchUnread = async () => {
    if (!gmailOn || !lead?.email) return;
    try {
      setLoadingUnread(true);

      const headers = signedInEmail ? { "X-User-Email": signedInEmail } : {};
      const params = signedInEmail ? { user_email: signedInEmail } : undefined;
      const encoded = encodeURIComponent(lead.email);

      const { data } = await api.get(
        `/integrations/gmail/unread-count/${encoded}`,
        { headers, params }
      );

      const count =
        typeof data?.unread_count === "number"
          ? data.unread_count
          : typeof data?.count === "number"
          ? data.count
          : 0;

      setUnread(count);
    } catch (e) {
      const code = e?.response?.status;
      if (code === 401 || code === 403 || code === 404) {
        setUnread(0);
        if (code === 404) {
          setGmailOn(false);
          clearInterval(pollTimerRef.current);
        }
        if (!muted404Ref.current) {
          muted404Ref.current = true;
          console.info("Unread badge disabled (gmail not connected). Code:", code);
        }
      } else {
        console.warn("Unread fetch failed:", e?.message || e);
      }
    } finally {
      setLoadingUnread(false);
    }
  };

  // ---------------------- FETCH CREATOR ----------------------
  const fetchCreatorName = async () => {
    if (!lead?.created_by) return;
    if (userCache[lead.created_by]) {
      setCreatorName(userCache[lead.created_by]);
      return;
    }
    try {
      const { data } = await api.get(`/users/${lead.created_by}`);
      if (data?.full_name) {
        userCache[lead.created_by] = data.full_name;
        setCreatorName(data.full_name);
      }
    } catch {
      /* no-op */
    }
  };

  // ---------------------- INITIAL LOAD ----------------------
  useEffect(() => {
    let mounted = true;
    (async () => {
      const available = await checkGmailAvailability(signedInEmail);
      if (!mounted) return;
      setGmailOn(available);
      if (available) {
        fetchUnread();
        pollTimerRef.current = setInterval(fetchUnread, 60000);
      }
    })();
    fetchCreatorName();
    return () => {
      mounted = false;
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [lead?.email, lead?.created_by, signedInEmail]);

  useEffect(() => {
    if (gmailOn) fetchUnread();
  }, [lead?.email, gmailOn]);

  // ---------------------- UI ACTIONS ----------------------
  const stop = (e) => {
    e.stopPropagation();
    e.preventDefault();
  };

  const onCall = (e) => {
    stop(e);
    const clean = (lead?.phone || "").replace(/\D/g, "");
    if (!clean) return;
    const callStart = new Date().toISOString();
    let ended = false;
    logActivity("Call", "Call initiated", { call_start: callStart, phone: clean });
    window.location.href = `tel:${clean}`;
    const finalize = (reason) => {
      if (ended) return;
      ended = true;
      const callEnd = new Date().toISOString();
      logActivity("Call", `Call ended (${reason})`, {
        call_start: callStart,
        call_end: callEnd,
        phone: clean,
      });
      document.removeEventListener("visibilitychange", handler);
      window.removeEventListener("focus", handler);
    };
    const handler = () => finalize("user returned");
    document.addEventListener("visibilitychange", handler);
    window.addEventListener("focus", handler);
    setTimeout(() => finalize("timeout fallback"), 120000);
  };

  const onWhatsApp = (e) => {
    stop(e);
    const clean = (lead?.phone || "").replace(/\D/g, "");
    if (!clean) {
      alert("No phone number found for this lead.");
      return;
    }
    const text = encodeURIComponent(
      `Hi ${lead.contact_person || ""}, this is from ${
        lead.business_name || "our team"
      }. Let's connect!`
    );
    window.open(`https://wa.me/${clean}?text=${text}`, "_blank");
    logActivity("WhatsApp", `Opened WhatsApp chat with ${clean}`, {
      phone: clean,
      verified_event: true,
    });
  };

  const onEmail = (e) => {
    stop(e);
    if (!lead?.email) {
      alert("No email found for this lead.");
      return;
    }
    setShowMail(true);
    logActivity("Email", "Email panel opened");
  };

  const handleMailSent = (meta = {}) => {
    logActivity("Email", "Email sent successfully", meta);
    fetchUnread();
  };

  const onActivityClick = (e) => {
    stop(e);
    onActivity?.();
  };

  // ---------------------- PRESENTATION ----------------------
  const stage = (lead.stage || "New").toString().toLowerCase();
  const stageColor =
    stage === "hot"
      ? "bg-red-500 text-white"
      : stage === "warm"
      ? "bg-amber-500 text-slate-900"
      : "bg-sky-500 text-white";

  let lastUpdated = "—";
  try {
    const ts = lead.updated_at || lead.last_updated || lead.created_at;
    if (ts) {
      const d = new Date(ts);
      if (!isNaN(d.getTime()))
        lastUpdated = d.toLocaleString("en-IN", {
          dateStyle: "medium",
          timeStyle: "short",
        });
    }
  } catch {}

  return (
    <>
      <div
        onClick={onView}
        className="group w-full rounded-xl bg-[#0C1428]/80 backdrop-blur-lg border border-white/10
                   hover:border-blue-400/50 hover:shadow-[0_0_20px_rgba(56,189,248,0.25)]
                   transition-all duration-300 overflow-hidden"
      >
        <div className="flex flex-col gap-2.5 p-4 md:p-5 w-full">
          <div className="flex items-center justify-between flex-wrap mb-1">
            <h3 className="text-base md:text-lg font-semibold text-white leading-tight">
              {lead.business_name || "—"}
            </h3>
            <span
              className={`px-2 py-0.5 text-[10px] md:text-xs rounded-full font-semibold ${stageColor}`}
            >
              {lead.stage || "New"}
            </span>
          </div>

          <div className="text-slate-300 text-xs md:text-sm">
            {lead.contact_person && (
              <span className="mr-1.5">{lead.contact_person}</span>
            )}
            {lead.city && <span className="text-slate-400">({lead.city})</span>}
          </div>

          <div
            className="flex flex-wrap gap-2 justify-start md:justify-end mt-2"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={onCall}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs md:text-sm font-medium shadow-sm"
            >
              <Phone size={14} /> Call
            </button>

            <button
              onClick={onWhatsApp}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-xs md:text-sm font-medium shadow-sm"
            >
              <MessageSquare size={14} /> WhatsApp
            </button>

            <button
              onClick={onEmail}
              className="relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs md:text-sm font-medium shadow-sm"
              title={gmailOn ? "Compose email" : "Gmail not connected"}
            >
              <Mail size={14} /> Email
              {gmailOn && unread > 0 && (
                <span
                  className={`absolute -top-1 -right-1 ${
                    unread >= 5 ? "animate-pulse" : ""
                  } bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center`}
                >
                  {unread}
                </span>
              )}
              {gmailOn && loadingUnread && (
                <span className="absolute -top-1 -right-1 w-4 h-4 border-2 border-white/80 border-t-transparent rounded-full animate-spin" />
              )}
            </button>

            <button
              onClick={onActivityClick}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-900 text-xs md:text-sm font-medium shadow-sm"
            >
              <ClipboardList size={14} /> Activity
            </button>
          </div>

          <div className="mt-1 text-[11px] md:text-xs text-slate-400 leading-tight">
            <div>
              Last Updated on{" "}
              <span className="text-slate-200">{lastUpdated}</span>
            </div>
            <div>
              Created By{" "}
              <span className="text-slate-200">{creatorName || "—"}</span>
            </div>
          </div>
        </div>
      </div>

      {showMail && (
  <div
    className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
    onClick={() => setShowMail(false)}  // closes when clicking outside
  >
    <div
      className="bg-[#0C1428] rounded-2xl shadow-2xl w-[95%] md:w-[85%] h-[90%] overflow-hidden border border-white/10 animate-fadeIn"
      onClick={(e) => e.stopPropagation()} // prevent closing when clicking inside
    >
      <MailPanel
        lead={lead}
        onClose={() => setShowMail(false)}
        onSent={(meta) => handleMailSent(meta)}
      />
    </div>
  </div>
)}
    </>
  );
}
