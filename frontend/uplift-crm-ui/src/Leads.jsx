// Leads.jsx — Unified with ActivityCenter Theme & AI Copilot
import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster, toast } from "react-hot-toast";
import CopilotHeader from "@/components/ai/CopilotHeader"; // ✅ 3D Robot Header
import LeadCard from "./components/LeadCard";
import LeadModal from "./components/LeadModal";
import ActivityModal from "./components/ActivityModal";
import client from "@/api/client";
import { useAICopilot } from "@/context/AICopilotContext";
import { useAI } from "@/hooks/useAI";

// --------------------------
const cls = (...a) => a.filter(Boolean).join(" ");

// --------------------------
export default function Leads({ token: tokenProp }) {
  const token = tokenProp || localStorage.getItem("uplift_token");

  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [viewLeadId, setViewLeadId] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [showActivity, setShowActivity] = useState(false);
  const [aiThinking, setAiThinking] = useState(false);
  const [copilotMsg, setCopilotMsg] = useState("");
  const msgTimer = useRef(null);

  const { insights, setInsights } = useAICopilot?.() || {
    insights: undefined,
    setInsights: () => {},
  };
  const { summarizeLead, analyzeLeads } = useAI();

  // --------------------------
  // Fetch leads
  async function loadLeads() {
    try {
      setLoading(true);
      const r = await client.get("/leads/");
      const arr = Array.isArray(r.data) ? r.data : [];
      setLeads(arr);
      await analyzeWithAI(arr);
    } catch (e) {
      console.error("Failed to fetch leads:", e);
      toast.error(e.response?.data?.detail || e.message || "Lead fetch failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) {
      toast.error("No token found");
      setLoading(false);
      return;
    }
    loadLeads();
  }, [token]);

  // --------------------------
  // AI Copilot logic
  const analyzeWithAI = async (list) => {
    if (!list?.length) return;
    try {
      setAiThinking(true);
      const res = await analyzeLeads(list);
      setInsights?.((prev) => ({
        ...(prev || {}),
        leads_summary: res,
      }));
    } catch (e) {
      console.warn("AI lead analysis unavailable, using fallback.");
      const active = list.filter((l) => l.is_active).length;
      const inactive = list.length - active;
      setInsights?.({
        total_leads: list.length,
        active_leads: active,
        inactive_leads: inactive,
        conversion_rate:
          list.length > 0 ? Math.round((active / list.length) * 100) : 0,
        top_source: "Referrals",
        growth_trend: "Stable",
      });
    } finally {
      setAiThinking(false);
    }
  };

  const popMsg = (text) => {
    setCopilotMsg(text);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    msgTimer.current = setTimeout(() => setCopilotMsg(""), 6000);
  };

  const handleSummarize = async (lead) => {
    try {
      setAiThinking(true);
      const out = await summarizeLead(encodeURIComponent(lead.id));
      const summary = out?.summary || "AI summary generated.";
      toast.success("AI Summary ready for lead.");
      setInsights?.((prev) => ({
        ...(prev || {}),
        lists: {
          ...(prev?.lists || {}),
          recent_ai_suggestions: [
            {
              id: lead.id,
              title: lead.business_name,
              type: "Lead",
              ai_suggestion: summary,
            },
            ...(prev?.lists?.recent_ai_suggestions || []),
          ],
        },
      }));
      popMsg("Lead summary ready!");
    } catch (e) {
      toast.error(`Summarize failed: ${e?.message || e}`);
    } finally {
      setAiThinking(false);
    }
  };

  // --------------------------
  const filteredLeads = useMemo(() => {
    const s = search.trim().toLowerCase();
    return !s
      ? leads
      : leads.filter((l) =>
          [l.business_name, l.contact_person, l.phone, l.city]
            .filter(Boolean)
            .some((v) => String(v).toLowerCase().includes(s))
        );
  }, [search, leads]);

  // --------------------------
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#060C20] via-[#0A1430] to-[#0C1428] text-slate-100 p-3 sm:p-4 md:p-6 grid grid-cols-1 xl:grid-cols-10 gap-4">
      <Toaster position="top-right" />

      <div className="xl:col-span-10 flex flex-col gap-4">
        {/* ✅ Copilot Header */}
        <CopilotHeader
          activities={leads}
          insights={{ ...insights, scope: "leads" }}
          onSummarizeAll={() =>
            leads.forEach((l) => handleSummarize(l))
          }
          onSuggestBulk={() => analyzeWithAI(leads)}
          aiPopMsg={copilotMsg}
          thinking={aiThinking}
        />

        {/* ---- Header ---- */}
        <div className="flex items-center justify-between mt-2">
          <h1 className="text-2xl md:text-3xl font-bold">Leads</h1>
          <button
            onClick={() => setCreating(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-yellow-400 hover:bg-yellow-300 text-slate-900 font-semibold shadow-[0_0_15px_rgba(250,204,21,0.3)] transition"
          >
            + Add New Lead
          </button>
        </div>

        {/* ---- Search ---- */}
        <div className="relative w-full md:w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search leads..."
            className="w-full pl-4 pr-3 py-2 rounded-xl bg-slate-800/60 border border-white/10 text-slate-100 placeholder:text-slate-400 focus:border-yellow-400/60 outline-none"
          />
        </div>

        {/* ---- Lead Stats ---- */}
        {/* ---- Lead Summary (Activity-Center Matched Design) ---- */}
<div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-2">
  <div className="bg-[#0B1330]/70 border border-white/10 rounded-2xl p-4 hover:border-blue-400/30 hover:shadow-[0_0_15px_rgba(56,189,248,0.25)] transition-all duration-300">
    <div className="text-[13px] md:text-sm text-slate-400 font-medium mb-1">
      🧩 Total Leads
    </div>
    <div className="text-2xl md:text-3xl font-bold text-white tracking-tight">
      {leads.length}
    </div>
    <div className="text-[11px] md:text-xs text-slate-500 mt-1">
      All active and archived leads
    </div>
  </div>

  <div className="bg-[#0B1330]/70 border border-white/10 rounded-2xl p-4 hover:border-emerald-400/30 hover:shadow-[0_0_15px_rgba(16,185,129,0.25)] transition-all duration-300">
    <div className="text-[13px] md:text-sm text-slate-400 font-medium mb-1">
      ⚡ Active Leads
    </div>
    <div className="text-2xl md:text-3xl font-bold text-emerald-300 tracking-tight">
      {leads.filter((l) => l.is_active).length}
    </div>
    <div className="text-[11px] md:text-xs text-slate-500 mt-1">
      Currently in active pipeline
    </div>
  </div>

  <div className="bg-[#0B1330]/70 border border-white/10 rounded-2xl p-4 hover:border-rose-400/30 hover:shadow-[0_0_15px_rgba(244,63,94,0.25)] transition-all duration-300">
    <div className="text-[13px] md:text-sm text-slate-400 font-medium mb-1">
      💤 Inactive Leads
    </div>
    <div className="text-2xl md:text-3xl font-bold text-rose-300 tracking-tight">
      {leads.filter((l) => !l.is_active).length}
    </div>
    <div className="text-[11px] md:text-xs text-slate-500 mt-1">
      Not engaged recently
    </div>
  </div>

  <div className="bg-[#0B1330]/70 border border-white/10 rounded-2xl p-4 hover:border-yellow-400/30 hover:shadow-[0_0_15px_rgba(250,204,21,0.25)] transition-all duration-300">
    <div className="text-[13px] md:text-sm text-slate-400 font-medium mb-1 flex justify-between items-center">
      🎯 Conversion Rate
      <span className="text-[11px] md:text-xs text-slate-500 font-normal">
        %
      </span>
    </div>
    <div className="text-2xl md:text-3xl font-bold text-yellow-300 tracking-tight">
      {leads.length
        ? Math.round(
            (leads.filter((l) => l.is_active).length / leads.length) * 100
          )
        : 0}
    </div>
    <div className="mt-2 h-2 rounded-full bg-slate-700 overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-yellow-400 to-orange-400 shadow-[0_0_8px_#facc15] transition-all duration-700"
        style={{
          width: `${
            leads.length
              ? (leads.filter((l) => l.is_active).length / leads.length) * 100
              : 0
          }%`,
        }}
      ></div>
    </div>
  </div>
</div>


        {/* ---- Lead List ---- */}
        <div className="space-y-3 mt-4">
          <AnimatePresence>
            {filteredLeads.map((lead) => (
              <motion.div
                key={lead.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <LeadCard
                  lead={lead}
                  onView={() => setViewLeadId(lead.id)}
                  onActivity={() => {
                    setSelectedLead(lead);
                    setShowActivity(true);
                  }}
                  onSummarize={() => handleSummarize(lead)}
                />
              </motion.div>
            ))}
            {!filteredLeads.length && (
              <div className="text-sm text-slate-400 text-center py-6">
                No leads found.
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* ---- Modals ---- */}
        {creating && (
          <LeadModal
            mode="create"
            onClose={() => setCreating(false)}
            onSaved={() => {
              setCreating(false);
              loadLeads();
            }}
          />
        )}

        {viewLeadId && (
          <LeadModal
            mode="view"
            leadId={viewLeadId}
            onClose={() => setViewLeadId(null)}
            onSaved={() => loadLeads()}
          />
        )}

        {showActivity && (
          <ActivityModal
            lead={selectedLead}
            onClose={() => setShowActivity(false)}
          />
        )}
      </div>
    </div>
  );
}
