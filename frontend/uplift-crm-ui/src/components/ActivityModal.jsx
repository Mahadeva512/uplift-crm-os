import React, { useEffect, useState, useRef } from "react";
import {
  X,
  PlusCircle,
  Phone,
  MessageSquare,
  Mail,
  FileText,
  MapPin,
  Clock,
  User,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/services/api";

export default function ActivityModal({ lead, onClose }) {
  const [activities, setActivities] = useState([]);
  const [newType, setNewType] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [outcome, setOutcome] = useState("");
  const [nextTask, setNextTask] = useState("");
  const [nextTaskDate, setNextTaskDate] = useState("");
  const [gps, setGps] = useState(null);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const scrollRef = useRef(null);
  const { user } = useAuthStore?.() || { user: {} };

  // ✅ Fetch activities (secured with token)
  const fetchActivities = async () => {
    if (!lead?.id) return;
    try {
      setLoading(true);
      const res = await api.get(`/activities`, {
        params: { lead_id: lead.id },
      });
      setActivities(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error("Activity fetch failed:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [lead?.id]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [activities]);

  // Capture GPS
  const getLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation not supported.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setGps({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        }),
      () => alert("Location access denied or failed.")
    );
  };

  // ✅ Add Activity (secured with token)
  const handleAdd = async () => {
    if (!newType || !newDesc.trim()) {
      alert("Please select type and enter description.");
      return;
    }

    const payload = {
      lead_id: lead.id,
      type: newType,
      title: `${newType} for ${lead.business_name}`,
      description: newDesc,
      status: "Pending",
      outcome: outcome || "—",
      assigned_to: user?.id,
      source_channel: "Manual",
      meta: {
        outcome,
        next_task: nextTask,
        next_task_date: nextTaskDate,
        gps,
      },
    };

    try {
      setAdding(true);
      await api.post(`/activities`, payload);
      setNewType("");
      setNewDesc("");
      setOutcome("");
      setNextTask("");
      setNextTaskDate("");
      setGps(null);
      await fetchActivities();
    } catch (err) {
      console.error("Create activity failed:", err);
    } finally {
      setAdding(false);
    }
  };

  const iconMap = {
    Call: Phone,
    WhatsApp: MessageSquare,
    Email: Mail,
    Visit: MapPin,
    Proposal: FileText,
    FollowUp: Clock,
  };

  const timeAgo = (iso) => {
    const diff = Date.now() - new Date(iso).getTime();
    if (diff < 60000) return "just now";
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    const days = Math.floor(hrs / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-[#0C1428]/95 w-full max-w-3xl rounded-2xl border border-white/10 p-6 relative text-white flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Activities — {lead.business_name}
            </h2>
            <p className="text-xs text-slate-400">
              View & log all actions linked to this lead
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition"
          >
            <X size={22} />
          </button>
        </div>

        {/* Activity list */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar"
        >
          {loading && (
            <p className="text-slate-400 text-sm italic">
              Loading activities…
            </p>
          )}
          {!loading && activities.length === 0 && (
            <p className="text-slate-400 text-sm italic">
              No activities found for this lead.
            </p>
          )}

          {activities.map((a, i) => {
            const Icon = iconMap[a.type] || FileText;
            return (
              <div
                key={a.id || i}
                className="flex items-start gap-3 bg-slate-800/30 border border-slate-700/40 rounded-xl p-3 hover:bg-slate-800/50 transition"
              >
                <div className="flex-shrink-0 mt-1">
                  <Icon size={18} className="text-blue-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sky-300">{a.type}</span>
                    <span className="text-xs text-slate-400">
                      {timeAgo(a.created_at)}
                    </span>
                  </div>
                  <p className="text-slate-200 text-sm leading-snug">
                    {a.description || "—"}
                  </p>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
                    <User size={12} /> {a.created_by_name || "Unknown"} •{" "}
                    Status:{" "}
                    <span
                      className={`font-semibold ${
                        a.status === "Completed"
                          ? "text-emerald-400"
                          : "text-amber-300"
                      }`}
                    >
                      {a.status}
                    </span>{" "}
                    • Outcome:{" "}
                    <span className="text-slate-300">{a.outcome || "—"}</span>
                    {a.call_duration && (
                      <>
                        {" "}
                        • ⏱ {Math.round(a.call_duration)} sec
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add new activity */}
        <div className="mt-4 border-t border-white/10 pt-4">
          <div className="flex flex-wrap gap-2 items-center mb-2">
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
              className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-400"
            >
              <option value="">Select Type</option>
              <option value="Call">Call</option>
              <option value="Visit">Visit</option>
              <option value="WhatsApp">WhatsApp</option>
              <option value="Email">Email</option>
              <option value="Proposal">Proposal</option>
              <option value="FollowUp">Follow-Up</option>
              <option value="Payment">Payment</option>
              <option value="Other">Other</option>
            </select>

            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={2}
              placeholder="Describe the activity..."
              className="flex-1 bg-slate-800/70 border border-slate-700 rounded-xl p-2 text-sm text-white resize-none focus:outline-none focus:border-blue-400"
            />
          </div>

          {/* Context fields */}
          {newType === "Call" && (
            <div className="flex flex-wrap gap-2 mb-2">
              <select
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              >
                <option value="">Select Call Outcome</option>
                <option value="Connected">Connected</option>
                <option value="Not Reached">Not Reached</option>
                <option value="Busy">Busy</option>
                <option value="Wrong Number">Wrong Number</option>
              </select>
              <input
                type="text"
                placeholder="Next Task"
                value={nextTask}
                onChange={(e) => setNextTask(e.target.value)}
                className="flex-1 bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              />
              <input
                type="date"
                value={nextTaskDate}
                onChange={(e) => setNextTaskDate(e.target.value)}
                className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              />
            </div>
          )}

          {newType === "Visit" && (
            <div className="flex flex-col gap-2 mb-2">
              <button
                onClick={getLocation}
                className="self-start bg-green-700 hover:bg-green-600 px-3 py-1 rounded-lg text-sm"
              >
                Capture Location
              </button>
              {gps && (
                <p className="text-xs text-slate-400">
                  Location: {gps.lat.toFixed(5)}, {gps.lng.toFixed(5)}
                </p>
              )}
              <input
                type="text"
                placeholder="Outcome / Notes"
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              />
              <input
                type="text"
                placeholder="Next Task"
                value={nextTask}
                onChange={(e) => setNextTask(e.target.value)}
                className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              />
              <input
                type="date"
                value={nextTaskDate}
                onChange={(e) => setNextTaskDate(e.target.value)}
                className="bg-slate-800/70 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-blue-400"
              />
            </div>
          )}

          {/* Add Button */}
          <button
            onClick={handleAdd}
            disabled={adding}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl px-4 py-2 shadow transition"
          >
            <PlusCircle size={16} /> {adding ? "Adding…" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}
