// ActivityCenter.jsx — Clean Final Build (with 3D CopilotHeader)
import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster, toast } from "react-hot-toast";
import CopilotHeader from "@/components/ai/CopilotHeader"; // ✅ 3D Robot Header

// ---- your app hooks (kept same names) ----
import { useActivitiesStore } from "../store/useActivitiesStore";
import { useAICopilot } from "@/context/AICopilotContext";
import { useAI } from "@/hooks/useAI";

const cls = (...a) => a.filter(Boolean).join(" ");
const fmt = (d) => (d ? new Date(d).toLocaleString() : "—");
const isTaskCompleted = (x) => ((x?.status || "").toLowerCase() === "completed");

// ---------- Small Helper UI ----------
const StatusBadge = ({ status }) => {
  const s = (status || "Pending").toLowerCase();
  const tone =
    s === "completed"
      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
      : s === "in-progress"
      ? "bg-sky-500/15 text-sky-300 border border-sky-500/25"
      : "bg-yellow-500/15 text-yellow-300 border border-yellow-500/25";
  return <span className={cls("text-[11px] px-2 py-0.5 rounded-md", tone)}>{status || "Pending"}</span>;
};

const PriorityDot = ({ p }) => {
  const map = {
    High: "bg-rose-400 shadow-[0_0_6px] shadow-rose-400/70",
    Medium: "bg-amber-300 shadow-[0_0_6px] shadow-amber-300/70",
    Low: "bg-emerald-300 shadow-[0_0_6px] shadow-emerald-300/70",
  };
  return <span title={`Priority: ${p || "—"}`} className={cls("inline-block w-2 h-2 rounded-full", map[p] || "bg-slate-400")} />;
};

const TypeIcon = ({ t }) => {
  const base = "inline-flex items-center justify-center w-6 h-6 rounded-md text-[12px]";
  const tone = "bg-slate-700/70 text-slate-200 border border-slate-600/40";
  const s = (t || "").toLowerCase();
  const symbol = s.includes("call") ? "📞" : s.includes("meet") ? "🗓️" : s.includes("email") ? "✉️" : s.includes("whatsapp") ? "💬" : "📌";
  return <span className={cls(base, tone)}>{symbol}</span>;
};

// ---------- Filters ----------
const FiltersBar = ({ scope, filters, setFilters, search, setSearch, onExport, view, setView, enableTimeline, enableKanban, leads }) => (
  <div className="rounded-2xl border border-white/10 bg-[#0B1330]/60 p-3 md:p-4 flex flex-col md:flex-row md:items-center gap-3">
    <div className="inline-flex rounded-xl p-1 bg-slate-800/60 border border-slate-700/60">
      <button onClick={() => setView("list")} className={cls("px-3 py-1.5 text-xs md:text-sm rounded-lg", view === "list" ? "bg-yellow-400 text-slate-900 shadow-[0_0_10px] shadow-yellow-400/40" : "text-slate-300")}>List</button>
      {enableTimeline && <button onClick={() => setView("timeline")} className={cls("px-3 py-1.5 text-xs md:text-sm rounded-lg", view === "timeline" ? "bg-yellow-400 text-slate-900 shadow-[0_0_10px] shadow-yellow-400/40" : "text-slate-300")}>Timeline</button>}
      {enableKanban && <button onClick={() => setView("kanban")} className={cls("px-3 py-1.5 text-xs md:text-sm rounded-lg", view === "kanban" ? "bg-yellow-400 text-slate-900 shadow-[0_0_10px] shadow-yellow-400/40" : "text-slate-300")}>Kanban</button>}
    </div>

    <div className="flex-1 grid grid-cols-2 md:grid-cols-6 gap-2">
      <input
      type="text"
      value={search}
      onChange={(e) => setSearch(e.target.value)}
      placeholder="Search by Lead Name..."
      className="bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-400"
     />

      <select className="bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200" value={filters.status} onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
        <option value="all">Status: All</option>
        <option>Pending</option>
        <option>In-Progress</option>
        <option>Completed</option>
      </select>
      <select className="bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200" value={filters.priority} onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
        <option value="all">Priority: All</option>
        <option>High</option><option>Medium</option><option>Low</option>
      </select>
      <select className="bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200" value={filters.type} onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value }))}>
        <option value="all">{scope === "tasks" ? "Task Type: All" : "Type: All"}</option>
        <option>Call</option><option>Meeting</option><option>Email</option><option>WhatsApp</option><option>Note</option><option>Follow-up</option>
      </select>
      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={`Search ${scope}…`} className="bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-400" />
      <button onClick={onExport} className="px-3 py-2 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200">Export CSV</button>
    </div>
  </div>
);

// ---------- Modal ----------
const Modal = ({ open, onClose, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="absolute inset-x-0 top-10 mx-auto max-w-3xl px-3">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="rounded-2xl border border-white/10 bg-[#0B1330]/80 backdrop-blur-xl p-4 shadow-[0_0_30px_rgba(0,72,232,0.2)]">
          {children}
        </motion.div>
      </div>
    </div>
  );
};

// ---------- Activity Card ----------
const ItemCard = ({ item, kind, ai, onOpen, onSummarize, onNextStep, onComplete }) => {
  const subtleGlow = "shadow-[0_0_0_1px_rgba(255,255,255,0.06)] hover:shadow-[0_0_0_1px_rgba(255,255,255,0.15),0_0_20px_#0048E8] transition-shadow";

  return (
    <div className={cls("rounded-3xl bg-[#0D1A37]/70 border border-white/10 p-4", subtleGlow)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <TypeIcon t={item.type || (kind === "task" ? "Task" : "Activity")} />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <div onClick={() => onOpen?.(item)} className="cursor-pointer text-left text-slate-100 font-semibold hover:text-yellow-300 truncate max-w-[80vw]">
                {item.title || item.type || "—"}
              </div>
              {item.status && <StatusBadge status={item.status} />}
              {item.priority && <PriorityDot p={item.priority} />}
            </div>

            <div className="text-xs text-slate-400 mt-1 truncate">
            {kind === "task" ? "Due: " : "When: "}
            {item.created_at ? fmt(item.created_at) : <span className="italic text-slate-500">No time recorded</span>}
            {item.created_by_name && <>{" · "}<span className="text-slate-300">Created By:</span> {item.created_by_name}</>}
            {item.assigned_to_name && <>{" · "}<span className="text-slate-300">Assigned:</span> {item.assigned_to_name}</>}
            {item.lead_name && <>{" · "}<span className="text-slate-300">Linked To:</span> {item.lead_name}</>}
            </div>


            {item.description && <p className="mt-2 text-sm text-slate-300 leading-relaxed">{item.description}</p>}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex gap-2">
            <button onClick={() => onSummarize(item)} className="text-xs px-3 py-1.5 rounded-full bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-100 active:scale-95">Summarize</button>
            <button onClick={() => onNextStep(item)} className="text-xs px-3 py-1.5 rounded-full bg-yellow-400 text-slate-900 hover:bg-yellow-300 active:scale-95">Next Step</button>
            {kind === "task" && !isTaskCompleted(item) && (
              <button onClick={() => onComplete(item)} className="text-xs px-3 py-1.5 rounded-full bg-emerald-500 text-slate-900 hover:bg-emerald-400 active:scale-95">Complete</button>
            )}
          </div>

          {/* AI summary preview */}
          {ai?.summary && <div className="text-[11px] text-emerald-300 italic truncate max-w-[42ch]">“{ai.summary.slice(0, 80)}{ai.summary.length > 80 ? "…" : ""}”</div>}
          {ai?.suggestion && <div className="text-[11px] text-yellow-300 italic truncate max-w-[42ch]">“{ai.suggestion.slice(0, 80)}{ai.suggestion.length > 80 ? "…" : ""}”</div>}
        </div>
      </div>

      {/* Inline AI section */}
      <details className="mt-3">
        <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-200">AI Insights</summary>
        <div className="mt-2 rounded-xl border border-slate-700 bg-slate-800/50 p-3 text-sm text-slate-200">
          {ai?.summary || ai?.suggestion ? (
            <>
              {ai?.summary && (<><b>Summary:</b> <span className="whitespace-pre-wrap">{ai.summary}</span><br /></>)}
              {ai?.suggestion && (<><b>Next Step:</b> <span className="whitespace-pre-wrap">{ai.suggestion}</span></>)}
            </>
          ) : (
            <span className="text-slate-400 italic">Click “Summarize” or “Next Step” to see AI suggestions.</span>
          )}
        </div>
      </details>
    </div>
  );
};

// ---------- Stats Panel ----------
function StatsPanel({ items, isTask }) {
  const totals = items?.length || 0;
  const completed = isTask ? (items?.filter(isTaskCompleted).length || 0) : 0;
  const pending = isTask ? (items?.filter((i) => !isTaskCompleted(i)).length || 0) : 0;
  const pct = isTask && totals ? Math.round((completed / totals) * 100) : 100;

  const Card = ({ label, value, accent }) => (
    <div className="rounded-2xl border border-white/10 bg-[#0B1330]/60 p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={cls("text-xl font-semibold", accent)}>{value}</div>
    </div>
  );

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Card label={isTask ? "Total Tasks" : "Total Activities"} value={totals} accent="text-slate-100" />
      {isTask && <Card label="Pending" value={pending} accent="text-yellow-300" />}
      {isTask && <Card label="Completed" value={completed} accent="text-emerald-300" />}

      <div className={cls("rounded-2xl border border-white/10 bg-[#0B1330]/60 p-3", isTask ? "" : "md:col-span-3")}>
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>{isTask ? "Completion" : "Activity Health"}</span>
          <span>{pct}%</span>
        </div>
        <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.6 }}
            className="h-full bg-gradient-to-r from-emerald-400 to-lime-300 rounded-full shadow-[0_0_8px_#10b981]" />
        </div>
      </div>
    </div>
  );
}

// ---------- Main ----------
export default function ActivityCenter({ onBack }) {
  const [activeTab, setActiveTab] = useState("activities");
  const [view, setView] = useState("list");
  const [filtersA, setFiltersA] = useState({ lead_id: "all", status: "all", priority: "all", type: "all" });
  const [filtersT, setFiltersT] = useState({ lead_id: "all", status: "all", priority: "all", type: "all" });
  const [searchA, setSearchA] = useState("");
  const [searchT, setSearchT] = useState("");
  const [pageA, setPageA] = useState(20);
  const [pageT, setPageT] = useState(20);
  const [activeItem, setActiveItem] = useState(null);
  const [aiMap] = useState(() => new Map());
  const [copilotMsg, setCopilotMsg] = useState("");
  const [aiThinking, setAiThinking] = useState(false);
  const msgTimer = useRef(null);

  const { activities, tasks, fetchActivities, completeTask } = useActivitiesStore();
  const { insights, setInsights } = useAICopilot?.() || { insights: undefined, setInsights: () => {} };
  const { summarizeActivity, suggestNextStep } = useAI();

  useEffect(() => { fetchActivities({}); }, [fetchActivities]);

  // Build lead dropdown
  const leads = useMemo(() => {
    const map = new Map();
    (activities || []).forEach((a) => { if (a.lead_id && !map.has(a.lead_id)) map.set(a.lead_id, { id: a.lead_id, name: a.lead_name || "Unnamed Lead" });});
    (tasks || []).forEach((t) => { if (t.lead_id && !map.has(t.lead_id)) map.set(t.lead_id, { id: t.lead_id, name: t.lead_name || "Lead" }); });
    return Array.from(map.values()).sort((x, y) => x.name.localeCompare(y.name));
  }, [activities, tasks]);

  // Filters logic
  const applyFilters = (list, f, search) => {
    let out = Array.isArray(list) ? list.slice() : [];
    if (f.lead_id !== "all") out = out.filter((i) => i.lead_id === f.lead_id);
    if (f.status !== "all") out = out.filter((i) => (i.status || "Pending") === f.status);
    if (f.priority !== "all") out = out.filter((i) => (i.priority || "—") === f.priority);
    if (f.type !== "all") out = out.filter((i) => (i.type || "").toLowerCase().includes(f.type.toLowerCase()));
    if (search?.trim()) {
      const q = search.trim().toLowerCase();
      out = out.filter((i) => (i.title || "").toLowerCase().includes(q) || (i.description || "").toLowerCase().includes(q) || (i.lead_name || "").toLowerCase().includes(q));
    }
    return out;
  };

  const fActivities = useMemo(() => applyFilters(activities, filtersA, searchA), [activities, filtersA, searchA]);
  const fTasks = useMemo(() => applyFilters(tasks, filtersT, searchT), [tasks, filtersT, searchT]);

  const pagedActivities = useMemo(() => fActivities.slice(0, pageA), [fActivities, pageA]);
  const pagedTasks = useMemo(() => fTasks.slice(0, pageT), [fTasks, pageT]);

  // -------- AI Actions --------
  const popMsg = (text) => {
    setCopilotMsg(text);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    msgTimer.current = setTimeout(() => setCopilotMsg(""), 6000);
  };

  const withThinking = async (fn) => {
    try {
      setAiThinking(true);
      await fn();
    } finally {
      setAiThinking(false);
    }
  };

  const handleSummarize = (item) =>
    withThinking(async () => {
      try {
        const out = await summarizeActivity(encodeURIComponent(item.id));
        const summary = out?.summary || out?.sentiment || JSON.stringify(out) || "Summary created.";
        aiMap.set(item.id, { ...(aiMap.get(item.id) || {}), summary });
        setInsights?.((prev) => ({
          ...(prev || {}),
          lists: { ...(prev?.lists || {}), recent_ai_suggestions: [{ id: item.id, title: item.title, type: item.type, ai_suggestion: summary }, ...(prev?.lists?.recent_ai_suggestions || [])] },
        }));
        toast.success("AI Summary generated.");
        popMsg("Summary ready! Open any card to view details.");
      } catch (e) {
        toast.error(`Summarize failed: ${e?.message || e}`);
      }
    });

  const handleNextStep = (item) =>
    withThinking(async () => {
      try {
        const out = await suggestNextStep(encodeURIComponent(item.id));
        const suggestion = out?.ai_suggestion || out?.suggestion || JSON.stringify(out) || "Next step generated.";
        aiMap.set(item.id, { ...(aiMap.get(item.id) || {}), suggestion });
        setInsights?.((prev) => ({
          ...(prev || {}),
          lists: { ...(prev?.lists || {}), recent_ai_suggestions: [{ id: item.id, title: item.title, type: item.type, ai_suggestion: suggestion }, ...(prev?.lists?.recent_ai_suggestions || [])] },
        }));
        toast.success("AI suggestion ready.");
        popMsg("New AI next steps added. Check the yellow lines on cards.");
      } catch (e) {
        toast.error(`Next Step failed: ${e?.message || e}`);
      }
    });

  const summarizeAll = () =>
    withThinking(async () => {
      if (!pagedActivities.length) return toast("No activities to summarize.");
      toast.loading("Summarizing all…", { id: "sumall" });
      for (const a of pagedActivities) await handleSummarize(a);
      toast.success("All summaries ready.", { id: "sumall" });
    });

  const planNextSteps = () =>
    withThinking(async () => {
      if (!pagedActivities.length) return toast("No activities to plan.");
      toast.loading("Generating next steps…", { id: "planall" });
      for (const a of pagedActivities) await handleNextStep(a);
      toast.success("Next steps suggested.", { id: "planall" });
    });

  const completeTaskSafe = async (t) => {
    try {
      await completeTask(t.id, "Completed");
      toast.success("Task completed 🎉");
    } catch (e) {
      toast.error(`Complete failed: ${e?.message || e}`);
    }
  };

  // -------- render --------
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#060C20] via-[#0A1430] to-[#0C1428] text-slate-100 p-3 sm:p-4 md:p-6 grid grid-cols-1 xl:grid-cols-10 gap-4">
      <Toaster position="top-right" />

      {/* Main column */}
      <div className="xl:col-span-10 flex flex-col gap-4">
        {/* Tabs */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="flex items-center gap-2">
            <button onClick={() => { setActiveTab("activities"); setView("list"); }}
              className={cls("px-4 py-2 rounded-xl text-sm font-semibold border",
                activeTab === "activities" ? "bg-yellow-400 text-slate-900 border-yellow-300 shadow-[0_0_20px] shadow-yellow-400/40" : "bg-slate-800/60 text-slate-300 border-white/10 hover:bg-slate-700/60")}>Activities</button>
            <button onClick={() => { setActiveTab("tasks"); setView("list"); }}
              className={cls("px-4 py-2 rounded-xl text-sm font-semibold border",
                activeTab === "tasks" ? "bg-yellow-400 text-slate-900 border-yellow-300 shadow-[0_0_20px] shadow-yellow-400/40" : "bg-slate-800/60 text-slate-300 border-white/10 hover:bg-slate-700/60")}>Tasks</button>
          </div>
          <button onClick={onBack} className="text-xs px-4 py-2 bg-slate-800/60 border border-white/10 rounded-xl hover:bg-slate-700/60">← Back</button>
        </div>

        {/* ✅ Copilot Header */}
        <CopilotHeader
        activities={activeTab === "tasks" ? fTasks : fActivities}
        insights={{ ...insights, scope: activeTab }}
        onSummarizeAll={summarizeAll}
        onSuggestBulk={planNextSteps}
        aiPopMsg={copilotMsg}
        thinking={aiThinking}
        />


        {/* Stats */}
        <StatsPanel items={activeTab === "activities" ? fActivities : fTasks} isTask={activeTab === "tasks"} />

        {/* Filters */}
        {activeTab === "activities" ? (
          <FiltersBar
            scope="activities"
            filters={filtersA}
            setFilters={setFiltersA}
            search={searchA}
            setSearch={setSearchA}
            onExport={() => exportCSV(fActivities, "activities.csv")}
            view={view}
            setView={setView}
            enableTimeline
            leads={leads}
          />
        ) : (
          <FiltersBar
            scope="tasks"
            filters={filtersT}
            setFilters={setFiltersT}
            search={searchT}
            setSearch={setSearchT}
            onExport={() => exportCSV(fTasks, "tasks.csv")}
            view={view}
            setView={setView}
            enableKanban
            leads={leads}
          />
        )}

        {/* List */}
        <div className="space-y-3">
          {activeTab === "activities" && (
            <AnimatePresence>
              {pagedActivities.map((a) => (
                <motion.div key={a.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
                  <ItemCard
                    item={a}
                    kind="activity"
                    ai={aiMap.get(a.id)}
                    onOpen={setActiveItem}
                    onSummarize={handleSummarize}
                    onNextStep={handleNextStep}
                  />
                </motion.div>
              ))}
              {!pagedActivities.length && <div className="text-sm text-slate-400 text-center py-6">No activities found</div>}
            </AnimatePresence>
          )}

          {activeTab === "tasks" && (
            <AnimatePresence>
              {pagedTasks.map((t) => (
                <motion.div key={t.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
                  <ItemCard
                    item={t}
                    kind="task"
                    ai={aiMap.get(t.id)}
                    onOpen={setActiveItem}
                    onSummarize={handleSummarize}
                    onNextStep={handleNextStep}
                    onComplete={completeTaskSafe}
                  />
                </motion.div>
              ))}
              {!pagedTasks.length && <div className="text-sm text-slate-400 text-center py-6">No tasks found</div>}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Modal */}
      <Modal open={!!activeItem} onClose={() => setActiveItem(null)}>
        {activeItem && (
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-lg font-semibold text-slate-100">{activeItem.title || activeItem.type || "—"}</div>
                <div className="text-xs text-slate-400 mt-1">
                  {(activeItem.__kind === "task" ? "Due: " : "When: ") + (activeItem.created_at ? fmt(activeItem.created_at) : "—")}
                  {activeItem.assigned_to_name && <>{" · "}<span className="text-slate-300">Assigned:</span> {activeItem.assigned_to_name}</>}
                  {activeItem.lead_name && <>{" · "}<span className="text-slate-300">Linked To:</span> {activeItem.lead_name}</>}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleSummarize(activeItem)} className="text-xs px-3 py-1.5 rounded-full bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-100">Summarize</button>
                <button onClick={() => handleNextStep(activeItem)} className="text-xs px-3 py-1.5 rounded-full bg-yellow-400 text-slate-900 hover:bg-yellow-300">Next Step</button>
                {activeItem.__kind === "task" && !isTaskCompleted(activeItem) && (
                  <button onClick={() => completeTaskSafe(activeItem)} className="text-xs px-3 py-1.5 rounded-full bg-emerald-500 text-slate-900 hover:bg-emerald-400">Complete</button>
                )}
              </div>
            </div>

            {activeItem.description && <p className="text-sm text-slate-300 leading-relaxed">{activeItem.description}</p>}

            <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-3 text-sm text-slate-200">
              {aiMap.get(activeItem.id)?.summary || aiMap.get(activeItem.id)?.suggestion ? (
                <>
                  {aiMap.get(activeItem.id)?.summary && (<><b>Summary:</b> <span className="whitespace-pre-wrap">{aiMap.get(activeItem.id).summary}</span><br /></>)}
                  {aiMap.get(activeItem.id)?.suggestion && (<><b>Next Step:</b> <span className="whitespace-pre-wrap">{aiMap.get(activeItem.id).suggestion}</span></>)}
                </>
              ) : (
                <span className="text-slate-400 italic">No AI output yet. Use the buttons above.</span>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// ---------- CSV util ----------
function exportCSV(rows, filename = "export.csv") {
  if (!rows?.length) return;
  const keys = Object.keys(rows[0]);
  const csv = [keys.join(","), ...rows.map((r) => keys.map((k) => JSON.stringify(r[k] ?? "")).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
