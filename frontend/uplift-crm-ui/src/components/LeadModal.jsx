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
import api from "@/services/api"; // ✅ Secure axios instance

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;

export default function LeadModal({ mode = "create", leadId, onClose, onSaved }) {
  const token = localStorage.getItem("uplift_token");
  const { user } = useAuthStore?.() || { user: {} };

  const [loading, setLoading] = useState(mode === "view");
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(mode === "create");
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    business_name: "",
    contact_person: "",
    email: "",
    phone: "",
    country: "",
    state: "",
    city: "",
    pincode: "",
    stage: "New",
    lat: 0,
    lng: 0,
    lead_source: "Field",
    next_action: "",
    notes: "",
  });

  const [activities, setActivities] = useState([]);
  const [nextTask, setNextTask] = useState(null);

  // ----------------- Helpers -----------------
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const blueFocus =
    "ring-1 ring-transparent hover:ring-[#00BFFF]/40 focus:ring-2 focus:ring-[#00BFFF] focus:outline-none transition-shadow";

  // ----------------- Fetch Lead -----------------
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

  // ----------------- Fetch Activities & Next Task -----------------
  const fetchActivities = async () => {
    if (!leadId) return;
    try {
      const r = await fetch(`${API_BASE}/activities?lead_id=${leadId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error("Failed to load activities");
      const data = await r.json();
      setActivities(data || []);
    } catch (e) {
      console.error("Activity fetch failed:", e);
    }
  };

  const fetchNextPlannedTask = async () => {
    if (!leadId) return;
    try {
      const r = await fetch(
        `${API_BASE}/activities?lead_id=${leadId}&status=Planned`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!r.ok) throw new Error("Failed to load next task");
      const data = await r.json();
      // pick earliest by due_date if available
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

  // ----------------- Duplicate Checks -----------------
  async function checkDuplicateField(field, value) {
  if (!value) return;
  try {
    const res = await fetch(
      `${API_BASE}/leads/check-duplicate?${field}=${encodeURIComponent(value)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) return;
    const data = await res.json();
    if (data.exists) {
      alert(`⚠️ A lead with this ${field} already exists.`);
    }
  } catch (e) {
    console.error("Duplicate check failed:", e);
  }
}


  async function checkDuplicate(phone) {
    const res = await fetch(`${API_BASE}/leads/check-duplicate?phone=${phone}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.exists;
  }

  // ----------------- Geolocation Autofill -----------------
  async function fetchAddressFromCoords(lat, lng) {
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
          pincode: get("postal_code"),
        }));
      }
    } catch (err) {
      console.error("Failed to fetch address:", err);
    }
  }

  useEffect(() => {
    if (mode === "create" && form.lead_source === "Field" && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = Number(pos.coords.latitude.toFixed(6));
          const lng = Number(pos.coords.longitude.toFixed(6));
          setForm((f) => ({ ...f, lat, lng }));
          fetchAddressFromCoords(lat, lng);
        },
        (err) => {
          console.error("Geolocation error:", err);
          alert("Unable to capture your location. Please enable location access.");
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  }, [form.lead_source, mode]);

  // ----------------- Activity Log (Create/Update) -----------------
  const logLeadActivity = async (leadData, actionType) => {
    try {
      if (!leadData?.id) return;
      const payload = {
        lead_id: leadData.id,
        type: actionType === "update" ? "Lead Update" : "Lead Creation",
        title:
          actionType === "update"
            ? `Lead Updated – ${leadData.business_name || "Lead"}`
            : `Lead Created – ${leadData.business_name || "Lead"}`,
        description:
          actionType === "update"
            ? "Lead details were modified."
            : "A new lead was added.",
        status: "Completed",
        outcome: "Recorded",
        assigned_to: user?.id,
        source_channel: "LeadModal",
        meta: { auto_logged: true },
      };
      await createActivity(payload);
      await fetchActivities();
      await fetchNextPlannedTask();
    } catch (err) {
      console.error("Lead activity log failed:", err);
    }
  };

  // ----------------- Save Handler -----------------
  async function handleSave() {
    setError("");
    setSaving(true);
    try {
      if (mode === "create") {
        const isDup = await checkDuplicate(form.phone);
        if (isDup) throw new Error("Duplicate lead detected with same phone number.");
      }

      const url =
        mode === "create" ? `${API_BASE}/leads/` : `${API_BASE}/leads/${leadId}`;
      const method = mode === "create" ? "POST" : "PUT";
      const r = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || `Save failed (${r.status})`);
      }

      const saved = await r.json().catch(() => ({}));
      onSaved?.();

      await logLeadActivity(saved || { id: leadId, ...form }, mode === "create" ? "create" : "update");

      if (mode === "create") onClose();
      else setIsEditing(false);
    } catch (e) {
      setError(e.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  // ----------------- Maps -----------------
  const googleMapSrc = useMemo(() => {
    const lat = form.lat || 0;
    const lng = form.lng || 0;
    return `https://www.google.com/maps?q=${lat},${lng}&z=15&output=embed`;
  }, [form.lat, form.lng]);

  const googleMapLink = `https://www.google.com/maps?q=${form.lat},${form.lng}`;

  // ----------------- UI -----------------
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#101B33] text-white rounded-2xl shadow-2xl w-[95%] md:w-[900px] max-h-[90vh] overflow-y-auto p-5 md:p-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 md:gap-0 px-4 py-3 md:px-6 md:py-4 border-b border-white/10">
          <div>
            <h2 className="text-white text-lg md:text-2xl font-semibold break-words">
              {mode === "create" ? "New Lead" : `Lead: ${form.business_name || "—"}`}
            </h2>
            {mode === "view" && (
              <p className="text-slate-300/80 text-sm mt-0.5">
                Stage: <span className="text-white/90">{form.stage || "New"}</span>
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 justify-end">
            {mode === "view" && !isEditing && (
              <>
                <a
                  className={`flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition ${blueFocus}`}
                  href={form.phone ? `tel:${form.phone}` : undefined}
                >
                  <Phone size={18} /> <span>Call</span>
                </a>
                <a
                className={`flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg transition ${blueFocus}`}
                href={
                form.phone
                ? `https://api.whatsapp.com/send?phone=${form.phone.replace(/\D/g, "")}&text=${encodeURIComponent(
                `Hi ${form.contact_person || ""}, this is from ${
                form.business_name || "our team"
                }. Let's connect!`
                )}`
                : undefined
                }
                target="_blank"
                rel="noreferrer"
                >
                <MessageSquare size={18} /> <span>WhatsApp</span>
                </a>
                <button
                  className={`flex items-center gap-1 bg-[#FACC15] hover:bg-[#e0b911] text-black px-3 py-1.5 rounded-lg transition ${blueFocus}`}
                  onClick={() => setIsEditing(true)}
                >
                  <Pencil size={18} /> <span>Edit Lead</span>
                </button>
              </>
            )}
            <button className="icon-btn" onClick={onClose} title="Close">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-6 pt-4 space-y-6">
          {error && (
            <div className="text-red-300 bg-red-500/10 border border-red-500/30 px-3 py-2 rounded">
              {error}
            </div>
          )}

          {loading ? (
            <div className="h-52 grid place-items-center text-slate-300">
              <Loader2 className="animate-spin mr-2" /> Loading...
            </div>
          ) : (
            <>
              {/* Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label="Business" name="business_name" value={form.business_name} onChange={handleChange} disabled={!isEditing} blueFocus={blueFocus} />
                <Field label="Contact" name="contact_person" value={form.contact_person} onChange={handleChange} disabled={!isEditing} blueFocus={blueFocus} />
                <Field label="Phone" name="phone" value={form.phone} onChange={handleChange} disabled={!isEditing} onBlur={() => checkDuplicateField("phone", form.phone)} blueFocus={blueFocus} />
                <Field label="Email" name="email" value={form.email} onChange={handleChange} disabled={!isEditing} onBlur={() => checkDuplicateField("email", form.email)} blueFocus={blueFocus} />
                <Field label="Country" name="country" value={form.country} onChange={handleChange} disabled={!isEditing || form.lead_source === "Field"} blueFocus={blueFocus} />
                <Field label="State" name="state" value={form.state} onChange={handleChange} disabled={!isEditing || form.lead_source === "Field"} blueFocus={blueFocus} />
                <Field label="City" name="city" value={form.city} onChange={handleChange} disabled={!isEditing || form.lead_source === "Field"} blueFocus={blueFocus} />
                <Field label="Pincode" name="pincode" value={form.pincode} onChange={handleChange} disabled={!isEditing || form.lead_source === "Field"} blueFocus={blueFocus} />

                {/* Stage */}
                <div>
                  <label className="lbl">STAGE</label>
                  <select
                    className={`inp ${blueFocus}`}
                    name="stage"
                    value={form.stage ?? ""}
                    onChange={handleChange}
                    disabled={!isEditing}
                  >
                    <option>New</option>
                    <option>Warm</option>
                    <option>Hot</option>
                    <option>Won</option>
                    <option>Lost</option>
                  </select>
                </div>

                {/* Lead Source */}
                <div>
                  <label className="lbl">LEAD SOURCE</label>
                  <select
                    className={`inp ${blueFocus}`}
                    name="lead_source"
                    value={form.lead_source ?? ""}
                    onChange={handleChange}
                    disabled={!isEditing}
                  >
                    <option>Field</option>
                    <option>WhatsApp</option>
                    <option>Email Campaign</option>
                    <option>Referral</option>
                    <option>Website</option>
                    <option>Inbound Call</option>
                    <option>Event</option>
                    <option>Other</option>
                  </select>
                </div>
                {/* REMOVED NEXT ACTION FIELD HERE:
                <Field label="Next Action" name="next_action" value={form.next_action} onChange={handleChange} disabled={!isEditing} blueFocus={blueFocus} />
                */}
              </div>

              {/* Notes */}
              <div>
                <label className="lbl">NOTES</label>
                <textarea
                  className={`inp h-28 ${blueFocus}`}
                  name="notes"
                  value={form.notes ?? ""}
                  onChange={handleChange}
                  disabled={!isEditing}
                  placeholder="Add remarks..."
                />
              </div>

              {/* Location */}
              <div>
                <div className="flex items-center gap-2 mb-2 text-slate-200">
                  <MapPin size={18} /> <span>Location Details</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                  <Field
                    label="Latitude"
                    name="lat"
                    value={form.lat}
                    onChange={(e) => setForm((f) => ({ ...f, lat: Number(e.target.value) }))}
                    // Added check to disable if lead_source is Field
                    disabled={!isEditing || form.lead_source === "Field"}
                    blueFocus={blueFocus}
                  />
                  <Field
                    label="Longitude"
                    name="lng"
                    value={form.lng}
                    onChange={(e) => setForm((f) => ({ ...f, lng: Number(e.target.value) }))}
                    // Added check to disable if lead_source is Field
                    disabled={!isEditing || form.lead_source === "Field"}
                    blueFocus={blueFocus}
                  />
                </div>

                <div className="rounded-xl overflow-hidden border border-white/10 shadow">
                  <iframe
                    title="map"
                    className="w-full h-64 md:h-72"
                    src={googleMapSrc}
                    style={{ border: 0 }}
                    loading="lazy"
                    allowFullScreen
                  />
                </div>
                <div className="mt-3 flex justify-end">
                  <a
                    href={googleMapLink}
                    target="_blank"
                    rel="noreferrer"
                    className={`flex items-center gap-2 text-[#00BFFF] hover:text-white hover:bg-[#00BFFF]/20 border border-[#00BFFF]/30 px-3 py-1.5 rounded-lg text-sm transition-all duration-300 ${blueFocus}`}
                  >
                    <ExternalLink size={16} /> View on Google Maps
                  </a>
                </div>
              </div>

              {/* Next Task */}
              <div className="mt-6">
                <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-100 mb-2">
                  <Clock size={18} /> Next Task
                </h3>
                {!nextTask ? (
                  <p className="text-slate-400 text-sm">No upcoming planned task yet.</p>
                ) : (
                  <div className="border border-white/10 rounded-lg px-3 py-2 bg-white/5">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-amber-300">{nextTask.title || nextTask.type}</span>
                      <span className="text-xs text-slate-400">
                        {nextTask.due_date
                          ? new Date(nextTask.due_date).toLocaleString("en-IN", {
                              dateStyle: "medium",
                              timeStyle: "short",
                            })
                          : "No due date"}
                      </span>
                    </div>
                    {nextTask.description && (
                      <div className="text-slate-300 mt-1">{nextTask.description}</div>
                    )}
                    <div className="text-xs text-slate-500 mt-0.5">
                      Status: {nextTask.status} {nextTask.outcome ? `| Outcome: ${nextTask.outcome}` : ""}
                    </div>
                  </div>
                )}
              </div>

              {/* Activity History */}
              <div className="mt-8">
                <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-100 mb-2">
                  <ClipboardList size={18} /> Activity History
                </h3>
                {activities.length === 0 ? (
                  <p className="text-slate-400 text-sm">No activities logged yet.</p>
                ) : (
                  <ul className="space-y-2 max-h-48 overflow-y-auto pr-2">
                    {activities.map((a) => (
                      <li
                        key={a.id}
                        className="border border-white/10 rounded-lg px-3 py-2 text-sm bg-white/5"
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-sky-400">{a.type}</span>
                          <span className="text-xs text-slate-400">
                            {new Date(a.created_at).toLocaleString("en-IN", {
                              dateStyle: "medium",
                              timeStyle: "short",
                            })}
                          </span>
                        </div>
                        {a.title && (
                          <div className="text-slate-200 mt-0.5">{a.title}</div>
                        )}
                        {a.description && (
                          <div className="text-slate-300 mt-1">{a.description}</div>
                        )}
                        <div className="text-xs text-slate-500 mt-0.5">
                          Status: {a.status} {a.outcome ? `| Outcome: ${a.outcome}` : ""}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex justify-end gap-3">
          <button
            className={`text-slate-300 hover:text-white hover:border-white border border-transparent px-4 py-2 rounded-lg transition ${blueFocus}`}
            onClick={onClose}
          >
            Cancel
          </button>
          {isEditing && (
            <button className={`btn ${blueFocus}`} onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
              <span className="ml-2">{mode === "create" ? "Save Lead" : "Save Changes"}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, name, value, onChange, disabled, placeholder, onBlur, blueFocus = "" }) {
  return (
    <div>
      <label className="lbl">{label.toUpperCase()}</label>
      <input
        className={`inp ${blueFocus}`}
        name={name}
        value={value ?? ""}
        onChange={onChange}
        disabled={disabled}
        placeholder={placeholder}
        onBlur={onBlur}
      />
    </div>
  );
}