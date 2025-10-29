// src/components/LeadModal.jsx
import React, { useEffect, useMemo, useState } from "react";
import {
  X,
  Phone,
  MessageSquare,
  Pencil,
  Save,
  MapPin,
  Loader2,
  ExternalLink,
  ClipboardList,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { createActivity } from "@/api/activities";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/services/api"; // ✅ single axios instance

// ✅ Use only VITE_API_URL (no localhost fallback)
const API_BASE = import.meta.env.VITE_API_URL;
const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;

export default function LeadModal({ mode = "create", leadId, onClose, onSaved }) {
  const token =
    localStorage.getItem("uplift_token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token");

  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    source: "",
    address: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
    lat: "",
    lng: "",
    notes: "",
  });
  const [activities, setActivities] = useState([]);
  const [nextTask, setNextTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const blueFocus =
    "ring-1 ring-transparent hover:ring-[#00BFFF]/40 focus:ring-2 focus:ring-[#00BFFF] focus:outline-none transition-shadow";

  // ---------- Load a lead (view/edit) ----------
  useEffect(() => {
    if (mode !== "view" || !leadId) return;
    let ignore = false;

    async function fetchLead() {
      try {
        setLoading(true);
        const { data } = await api.get(`/leads/${leadId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!ignore) setForm((f) => ({ ...f, ...data }));
      } catch (e) {
        console.error("Failed to load lead:", e);
        setError(e.message || "Failed to load lead");
      } finally {
        setLoading(false);
      }
    }

    fetchLead();
    return () => { ignore = true; };
  }, [mode, leadId, token]);

  // ---------- Activities & Next Task ----------
  const fetchActivities = async () => {
    if (!leadId) return;
    try {
      const { data } = await api.get(`/activities`, {
        params: { lead_id: leadId },
        headers: { Authorization: `Bearer ${token}` },
      });
      setActivities(data || []);
    } catch (e) {
      console.error("Activity fetch failed:", e);
    }
  };

  const fetchNextPlannedTask = async () => {
    if (!leadId) return;
    try {
      const { data } = await api.get(`/activities/next-planned`, {
        params: { lead_id: leadId },
        headers: { Authorization: `Bearer ${token}` },
      });
      const sorted = (data || []).sort((a, b) => {
        const da = a?.due_date ? new Date(a.due_date).getTime() : Infinity;
        const db = b?.due_date ? new Date(b.due_date).getTime() : Infinity;
        return da - db;
      });
      setNextTask(sorted[0] || null);
    } catch (e) {
      console.error("Next task fetch failed:", e);
    }
  };

  useEffect(() => {
    if (leadId) {
      fetchActivities();
      fetchNextPlannedTask();
    }
  }, [leadId]);

  // ---------- Duplicate checks ----------
  async function checkDuplicateField(field, value) {
    if (!value) return;
    try {
      const { data } = await api.get(`/leads/check-duplicate`, {
        params: { [field]: value },
        headers: { Authorization: `Bearer ${token}` },
      });
      if (data?.exists) {
        alert(`⚠️ A lead with this ${field} already exists.`);
      }
    } catch (e) {
      // ignore soft-fail
    }
  }
  const checkDuplicate = async (phone) => {
    if (!phone) return false;
    try {
      const { data } = await api.get(`/leads/check-duplicate`, {
        params: { phone },
        headers: { Authorization: `Bearer ${token}` },
      });
      return !!data?.exists;
    } catch {
      return false;
    }
  };

  // ---------- Save lead (create/update) ----------
  const saveLead = async () => {
    try {
      setSaving(true);
      setError("");

      if (mode === "create" && form.phone) {
        const isDup = await checkDuplicate(form.phone);
        if (isDup) throw new Error("Duplicate lead detected with same phone number.");
      }

      const payload = { ...form };
      let saved;

      if (mode === "create") {
        const { data } = await api.post(`/leads`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        saved = data;
      } else {
        const { data } = await api.put(`/leads/${leadId}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        saved = data;
      }

      // optional hook
      onSaved && onSaved(saved);
      onClose && onClose();
    } catch (e) {
      console.error("Save lead failed", e);
      setError(e.message || "Failed to save lead");
    } finally {
      setSaving(false);
    }
  };

  // ---------- Reverse geocode (Google) ----------
  async function reverseGeocode(lat, lng) {
    try {
      const r = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${GOOGLE_API_KEY}`
      );
      const data = await r.json();
      if (data.results && data.results[0]) {
        const comps = data.results[0].address_components;
        const get = (type) => {
          const c = comps.find((x) => x.types.includes(type));
          return c ? c.long_name : "";
        };
        setForm((f) => ({
          ...f,
          country: get("country"),
          state: get("administrative_area_level_1"),
          city: get("locality") || get("administrative_area_level_2"),
        }));
      }
    } catch (e) {
      // non-blocking
    }
  }

  // ---------- UI bits (unchanged layout) ----------
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (["phone", "email"].includes(name)) checkDuplicateField(name, value);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-[#0B1222] border border-white/10 rounded-2xl shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h2 className="text-white font-semibold">{mode === "create" ? "Create Lead" : "View Lead"}</h2>
          <button onClick={onClose} className="text-slate-300 hover:text-white"><X size={20} /></button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-3">
          {error && <div className="text-red-400 text-sm">{error}</div>}

          {/* Basic fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="name" placeholder="Name" value={form.name} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="phone" placeholder="Phone" value={form.phone} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="email" placeholder="Email" value={form.email} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="source" placeholder="Source" value={form.source} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="address" placeholder="Address" value={form.address} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="city" placeholder="City" value={form.city} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="state" placeholder="State" value={form.state} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="country" placeholder="Country" value={form.country} onChange={onChange} />
            <input className={`bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} name="pincode" placeholder="Pincode" value={form.pincode} onChange={onChange} />
          </div>

          {/* Notes */}
          <textarea className={`w-full bg-[#0E1630] text-white px-3 py-2 rounded ${blueFocus}`} rows={3} name="notes" placeholder="Notes" value={form.notes} onChange={onChange} />

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={onClose} className="px-3 py-2 bg-slate-600/30 text-slate-200 rounded-lg hover:bg-slate-600/50">Cancel</button>
            <button disabled={saving} onClick={saveLead} className="px-3 py-2 bg-[#00BFFF] text-[#0B1222] rounded-lg hover:opacity-90 flex items-center gap-2">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              {saving ? "Saving..." : (mode === "create" ? "Create" : "Save")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
