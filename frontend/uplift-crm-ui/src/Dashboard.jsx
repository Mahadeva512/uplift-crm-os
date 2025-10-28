// src/components/Dashboard.jsx
import React, { useEffect, useMemo, useState } from "react";
import OnboardingModal from "./OnboardingModal";

/** ====== BRAND ICONS (inline; no external assets) ====== */
const RobotIcon = ({ className = "w-6 h-6" }) => (
  <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
    <defs>
      <linearGradient id="upliftGlow" x1="0" x2="1">
        <stop offset="0" stopColor="#38BDF8" />
        <stop offset="1" stopColor="#60A5FA" />
      </linearGradient>
    </defs>
    <rect x="8" y="16" width="48" height="36" rx="10" fill="url(#upliftGlow)" />
    <circle cx="26" cy="34" r="4" fill="#0C1428" />
    <circle cx="38" cy="34" r="4" fill="#0C1428" />
    <rect x="18" y="40" width="28" height="4" rx="2" fill="#0C1428" opacity="0.25" />
    <rect x="30" y="8" width="4" height="8" rx="2" fill="#38BDF8" />
  </svg>
);

/** ====== FEATURE FLAGS (tenant-level switches) ====== */
const FEATURES = {
  automation: true,
  campaigns: true,
  inventory: true,
  finance: true,
  tickets: true,
  hr: false, // available later
};

export default function Dashboard({ onLogout, onSwitch }) {
  const [user, setUser] = useState(null);
  const [company, setCompany] = useState(null);
  const [showCompanyModal, setShowCompanyModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // UI state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileMoreOpen, setMobileMoreOpen] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(true); // desktop open by default
  const [activeBottom, setActiveBottom] = useState("home"); // home | leads | activities | deals | more

  const API_BASE = useMemo(() => {
    const env = import.meta.env?.VITE_API_BASE_URL?.trim();
    if (env) return env.replace(/\/+$/, "");
    const host = window.location.hostname || "localhost";
    return `http://${host}:8000`;
  }, []);

  // 🧠 Load session + company
  useEffect(() => {
    const token = localStorage.getItem("uplift_token");
    async function loadData() {
      try {
        const u = JSON.parse(localStorage.getItem("uplift_user") || "{}");
        setUser(u);

        const res = await fetch(`${API_BASE}/company/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setCompany(data);
          localStorage.setItem("uplift_company", JSON.stringify(data));
          if (
            data?.company_name?.endsWith("’s Company") ||
            data?.company_name?.endsWith("'s Company")
          ) {
            setShowCompanyModal(true);
          }
        } else {
          setShowCompanyModal(true);
        }
      } catch (err) {
        console.error("❌ Company load error:", err);
        setShowCompanyModal(true);
      } finally {
        setLoading(false);
      }
    }
    setTimeout(loadData, 400);
  }, [API_BASE]);

  // 🔧 Update company info
  async function updateCompany(data) {
    try {
      const token = localStorage.getItem("uplift_token");
      const res = await fetch(`${API_BASE}/company/update`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Update failed");
      const updated = await res.json();
      localStorage.setItem("uplift_company", JSON.stringify(updated));
      setCompany(updated);
      setShowCompanyModal(false);
    } catch (err) {
      console.error("Company update failed:", err);
      alert("Could not update company info.");
    }
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#0C1428] text-white">
        <div className="animate-pulse text-lg">Loading your workspace…</div>
      </div>
    );
  }

  /** ====== PLACEHOLDER DATA (wire endpoints later) ====== */
  const kpis = [
    { title: "New Leads Today", value: "18", change: "+12%" },
    { title: "Active Opportunities", value: "₹4.6L" },
    { title: "Revenue This Month", value: "₹2.8L" },
    { title: "Activities Due Today", value: "12" },
    { title: "Accounts Added", value: "5" },
    { title: "Contacts Added", value: "23" },
  ];

  const activities = [
    { text: "Karthik updated quotation #Q-104", time: "2 hrs ago" },
    { text: "Follow-up call scheduled for tomorrow", time: "5 hrs ago" },
    { text: "Lead converted to Account", time: "Today" },
  ];

  const workflowSummary = { runsToday: 7, failed: 1, approvalsPending: 2 };
  const campaigns = [
    { name: "Diwali Promo", leads: 14 },
    { name: "Walk-in Offers", leads: 6 },
    { name: "Instagram DMs", leads: 9 },
  ];
  const accountsTop = [
    { name: "Kiara Furnishings", open: "₹1.2L" },
    { name: "Alpapine Uniforms", open: "₹95k" },
    { name: "Varalakshmi Silks", open: "₹70k" },
  ];
  const contactsRecent = [
    { name: "Karthik R", activity: "Opened quote", when: "1h" },
    { name: "Nisha P", activity: "Replied on WhatsApp", when: "3h" },
    { name: "Rahul S", activity: "Call scheduled", when: "Today" },
  ];
  const inventoryAlerts = [{ sku: "UNIF-POLO-NVY-M", low: 12 }, { sku: "SAREE-GOLD-6Y", low: 5 }];
  const ordersPending = [{ id: "SO-104", age: "2d" }, { id: "SO-105", age: "1d" }];
  const finance = { collected: "₹2.1L", outstanding: "₹1.6L", invoicesDue: 4 };
  const ticketsPanel = [{ id: "TCK-42", title: "Alteration request", age: "1d" }, { id: "TCK-43", title: "Delivery ETA", age: "6h" }];

  /** ====== Small UI helpers ====== */
  const NavItem = ({ label, onClick, active, disabled }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full text-left flex items-center gap-3 px-3 py-2 rounded-lg transition
        ${active ? "bg-white/10 text-white" : "text-white/80 hover:bg-white/5"}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <span className="text-sm">{label}</span>
    </button>
  );

  /** ====== VIEW ====== */
  return (
    <div className="h-screen w-full bg-[#0C1428] text-white flex">
      {/* Sidebar (desktop) */}
      <aside className="hidden lg:flex lg:w-72 flex-col border-r border-white/10">
        <div className="px-5 py-4">
          <div className="text-[#FFD700] font-bold tracking-wide">UPLIFT CRM OS</div>
          <div className="text-xs text-white/50 mt-1">{company?.company_name || "Your Company"}</div>
        </div>
        <div className="px-3 space-y-1 pb-4 overflow-y-auto">
          <NavItem label="Dashboard" active />
          <NavItem label="Leads" onClick={() => onSwitch?.("leads")} />
          <NavItem label="Opportunities / Deals" disabled />
          <NavItem label="Accounts" disabled />
          <NavItem label="Contacts" disabled />
          <NavItem label="Activity Center" onClick={() => onSwitch?.("activity-center")} />
          <NavItem label="Tasks" disabled />
          <NavItem label="Quotations" disabled />
          <NavItem label="Orders / Sales" disabled />
          <NavItem label="Payments / Invoices" disabled />
          <NavItem label="Products / Inventory" disabled />
          <NavItem label="Tickets / Projects" disabled />
          <NavItem label="Workflow & Automation" disabled />
          <NavItem label="Campaigns / Marketing" disabled />
          <NavItem label="Documents / Files" disabled />
          <NavItem label="Reports & Analytics" disabled />
          <NavItem label="Integrations" disabled />
          <div className="border-t border-white/10 my-2" />
          <NavItem label="Company Settings" onClick={() => setShowCompanyModal(true)} />
          <NavItem label="Logout" onClick={onLogout} />
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-40 bg-[#0C1428]/95 backdrop-blur border-b border-white/10">
        <div className="h-14 flex items-center justify-between px-4">
          <button onClick={() => setMobileMenuOpen(true)} className="rounded-lg px-3 py-1 bg-white/5 text-sm">☰</button>
          <div className="text-[#FFD700] font-semibold">UPLIFT CRM OS</div>
          <button
            onClick={() => setCopilotOpen((s) => !s)}
            className="p-1 rounded-full bg-white/5"
            title="Toggle Co-Pilot"
          >
            <RobotIcon className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Mobile sidebar drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-80 bg-[#0C1428] border-r border-white/10 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="text-[#FFD700] font-bold">UPLIFT CRM OS</div>
              <button className="rounded-lg px-2 py-1 bg-white/5 text-sm" onClick={() => setMobileMenuOpen(false)}>✕</button>
            </div>
            <div className="space-y-1">
              <NavItem label="Dashboard" active onClick={() => setMobileMenuOpen(false)} />
              <NavItem label="Leads" onClick={() => { setMobileMenuOpen(false); onSwitch?.("leads"); }} />
              <NavItem label="Opportunities / Deals" disabled />
              <NavItem label="Accounts" disabled />
              <NavItem label="Contacts" disabled />
              <NavItem label="Activity Center" onClick={() => { setMobileMenuOpen(false); onSwitch?.("activity-center"); }} />
              <NavItem label="Tasks" disabled />
              <NavItem label="Quotations" disabled />
              <NavItem label="Orders / Sales" disabled />
              <NavItem label="Payments / Invoices" disabled />
              <NavItem label="Products / Inventory" disabled />
              <NavItem label="Tickets / Projects" disabled />
              <NavItem label="Workflow & Automation" disabled />
              <NavItem label="Campaigns / Marketing" disabled />
              <NavItem label="Documents / Files" disabled />
              <NavItem label="Reports & Analytics" disabled />
              <NavItem label="Integrations" disabled />
              <div className="border-t border-white/10 my-2" />
              <NavItem label="Company Settings" onClick={() => { setMobileMenuOpen(false); setShowCompanyModal(true); }} />
              <NavItem label="Logout" onClick={() => { setMobileMenuOpen(false); onLogout?.(); }} />
            </div>
          </div>
        </div>
      )}

      {/* Main Column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar (desktop) */}
        <header className="hidden lg:flex items-center justify-between bg-[#0C1428]/95 backdrop-blur p-4 border-b border-white/10">
          <div>
            <div className="text-2xl font-semibold">Dashboard</div>
            <div className="text-xs text-white/50">
              Welcome {user?.name ? `, ${user.name}` : ""} · {company?.company_name || "Your Company"}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <input
                className="bg-[#0F172A] text-white text-sm pl-3 pr-10 py-2 rounded-lg focus:outline-none w-72 border border-white/10 placeholder:text-white/40"
                placeholder="Search…"
              />
              <span className="absolute right-3 top-2.5 text-white/40">🔍</span>
            </div>
            <button className="px-3 py-2 rounded-lg bg-white/5">🔔</button>
            <button
              onClick={() => setCopilotOpen((s) => !s)}
              className="px-3 py-2 rounded-lg bg-white/5 flex items-center gap-2"
              title="Toggle Co-Pilot"
            >
              <RobotIcon />
              <span className="hidden xl:inline text-sm">Co-Pilot</span>
            </button>
          </div>
        </header>

        {/* Content Row */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Main Dashboard */}
          <main className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6">
            {/* Spacer for mobile topbar height */}
            <div className="lg:hidden h-14" />

            {/* KPI Cards (includes Accounts/Contacts) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-4">
              {kpis.map((k, i) => (
                <div key={i} className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                  <div className="text-white/70 text-sm mb-2">{k.title}</div>
                  <div className="flex items-end justify-between">
                    <div className="text-2xl font-semibold">{k.value}</div>
                    {k.change && <div className="text-emerald-400 text-xs">{k.change}</div>}
                  </div>
                </div>
              ))}
            </div>

            {/* Row: Funnel + Activity Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Funnel */}
              <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                <div className="text-sm text-white/80 mb-3">Funnel Overview</div>
                {[
                  { label: "LEADS", count: 122, w: "w-[95%]" },
                  { label: "OPPORTUNITIES", count: 64, w: "w-[75%]" },
                  { label: "QUOTATIONS", count: 41, w: "w-[55%]" },
                  { label: "ORDERS", count: 25, w: "w-[38%]" },
                  { label: "PAYMENTS", count: 18, w: "w-[30%]" },
                ].map((s, idx) => (
                  <div key={idx} className="mb-3">
                    <div className={`h-9 ${s.w} rounded-xl bg-gradient-to-r from-[#38BDF8]/70 to-[#1d4ed8]/60 flex items-center px-4`}>
                      <div className="text-xs font-semibold tracking-wide">{s.label}</div>
                      <div className="ml-auto text-xs text-white/80">({s.count})</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Activity Timeline */}
              <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                <div className="text-sm text-white/80 mb-3">Activity Timeline</div>
                <ul className="space-y-3">
                  {activities.map((a, i) => (
                    <li key={i} className="border-l-2 border-[#38BDF8] pl-3">
                      <div className="text-sm">{a.text}</div>
                      <div className="text-xs text-white/50">{a.time}</div>
                    </li>
                  ))}
                </ul>

                {/* Quick Actions row (functional) */}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button onClick={() => onSwitch?.("leads")} className="px-3 py-2 text-sm rounded-lg bg-white/10 hover:bg-white/15 transition">Go to Leads</button>
                  <button onClick={() => onSwitch?.("activity-center")} className="px-3 py-2 text-sm rounded-lg bg-white/10 hover:bg-white/15 transition">Activity Center</button>
                  <button onClick={() => setShowCompanyModal(true)} className="px-3 py-2 text-sm rounded-lg bg-white/10 hover:bg-white/15 transition">Company Settings</button>
                  <button onClick={onLogout} className="px-3 py-2 text-sm rounded-lg bg-white/10 hover:bg-white/15 transition">Logout</button>
                </div>
              </div>
            </div>

            {/* Row: Workflow & Automation + Campaigns Pulse */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Workflow & Automation */}
              {FEATURES.automation && (
                <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm text-white/80">Workflow & Automation</div>
                    <span className="text-xs text-white/50">Status today</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="bg-white/5 rounded-xl p-3">
                      <div className="text-2xl font-semibold">{workflowSummary.runsToday}</div>
                      <div className="text-xs text-white/60 mt-1">Runs</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                      <div className="text-2xl font-semibold text-rose-400">{workflowSummary.failed}</div>
                      <div className="text-xs text-white/60 mt-1">Failed</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                      <div className="text-2xl font-semibold text-amber-300">{workflowSummary.approvalsPending}</div>
                      <div className="text-xs text-white/60 mt-1">Approvals</div>
                    </div>
                  </div>
                  <div className="mt-4 text-xs text-white/50">Automations run on triggers (lead created, status changed, due today, etc.).</div>
                </div>
              )}

              {/* Campaigns Pulse */}
              {FEATURES.campaigns && (
                <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                  <div className="text-sm text-white/80 mb-3">Campaigns Pulse</div>
                  <div className="space-y-2">
                    {campaigns.map((c, i) => (
                      <div key={i} className="flex items-center gap-3 bg-white/5 rounded-xl px-3 py-2">
                        <div className="w-2 h-2 rounded-full bg-[#38BDF8]" />
                        <div className="text-sm">{c.name}</div>
                        <div className="ml-auto text-xs text-white/70">{c.leads} leads</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 text-xs text-white/50">Lead Sources · WhatsApp · Ads · Referrals</div>
                </div>
              )}
            </div>

            {/* Row: Accounts/Contacts snapshot + Inventory/Orders + Finance + Tickets */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Accounts & Contacts Snapshot */}
              <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                <div className="text-sm text-white/80 mb-3">Accounts & Contacts Snapshot</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-white/50 mb-2">Top Accounts by Open Value</div>
                    <ul className="space-y-2">
                      {accountsTop.map((a, i) => (
                        <li key={i} className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 text-sm">
                          <span className="w-2 h-2 bg-[#FFD700] rounded-full" />
                          <span className="truncate">{a.name}</span>
                          <span className="ml-auto text-white/70">{a.open}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <div className="text-xs text-white/50 mb-2">Recent Contacts Engaged</div>
                    <ul className="space-y-2">
                      {contactsRecent.map((c, i) => (
                        <li key={i} className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 text-sm">
                          <span className="w-2 h-2 bg-[#38BDF8] rounded-full" />
                          <span className="truncate">{c.name}</span>
                          <span className="ml-auto text-white/60 text-xs">{c.activity} · {c.when}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Enterprise row: Inventory/Orders + Finance + Tickets */}
              <div className="grid grid-cols-1 gap-6">
                {/* Inventory & Orders */}
                {FEATURES.inventory && (
                  <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                    <div className="text-sm text-white/80 mb-3">Inventory Alerts & Pending Orders</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-white/50 mb-2">Low Stock</div>
                        <ul className="space-y-2">
                          {inventoryAlerts.map((it, i) => (
                            <li key={i} className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 text-sm">
                              <span className="w-2 h-2 bg-rose-400 rounded-full" />
                              <span className="truncate">{it.sku}</span>
                              <span className="ml-auto text-white/70">Qty {it.low}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="text-xs text-white/50 mb-2">Orders Awaiting Fulfillment</div>
                        <ul className="space-y-2">
                          {ordersPending.map((o, i) => (
                            <li key={i} className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 text-sm">
                              <span className="w-2 h-2 bg-amber-300 rounded-full" />
                              <span>{o.id}</span>
                              <span className="ml-auto text-white/70">{o.age}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Finance Snapshot */}
                {FEATURES.finance && (
                  <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                    <div className="text-sm text-white/80 mb-3">Finance Snapshot</div>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div className="bg-white/5 rounded-xl p-3">
                        <div className="text-2xl font-semibold">{finance.collected}</div>
                        <div className="text-xs text-white/60 mt-1">Collected</div>
                      </div>
                      <div className="bg-white/5 rounded-xl p-3">
                        <div className="text-2xl font-semibold">{finance.outstanding}</div>
                        <div className="text-xs text-white/60 mt-1">Outstanding</div>
                      </div>
                      <div className="bg-white/5 rounded-xl p-3">
                        <div className="text-2xl font-semibold">{finance.invoicesDue}</div>
                        <div className="text-xs text-white/60 mt-1">Invoices Due</div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-white/50">Wire to: /api/finance/ar-ap/summary</div>
                  </div>
                )}

                {/* Tickets / Projects */}
                {FEATURES.tickets && (
                  <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-4 shadow-lg">
                    <div className="text-sm text-white/80 mb-3">Tickets / Projects</div>
                    <ul className="space-y-2">
                      {ticketsPanel.map((t, i) => (
                        <li key={i} className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 text-sm">
                          <span className="w-2 h-2 bg-emerald-400 rounded-full" />
                          <span className="truncate">{t.id} · {t.title}</span>
                          <span className="ml-auto text-white/70">{t.age}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </main>

          {/* AI Co-Pilot (desktop drawer) */}
          <aside
            className={`hidden lg:flex w-[340px] flex-col border-l border-white/10 bg-[#0F172A] transition-transform ${
              copilotOpen ? "translate-x-0" : "translate-x-full"
            }`}
          >
            <div className="p-5 border-b border-white/10 flex items-center gap-3">
              <RobotIcon className="w-7 h-7" />
              <div className="text-[#FFD700] font-semibold text-sm">Uplift Co-Pilot</div>
            </div>
            <div className="p-5 space-y-4 text-sm">
              <div className="text-white/80">Smart suggestions</div>
              <ul className="space-y-3">
                <li>✅ Top 3 stalled deals</li>
                <li>📞 Leads likely to convert this week</li>
                <li>✍️ Suggested follow-up message</li>
                <li>📁 Account health snapshot</li>
              </ul>
              <div className="pt-2">
                <input
                  className="w-full bg-[#0C1428] border border-white/10 rounded-lg px-3 py-2 text-sm placeholder:text-white/40"
                  placeholder="Ask Uplift anything…"
                />
              </div>
            </div>
          </aside>
        </div>
      </div>

      {/* Floating Co-Pilot button (mobile) */}
      <button
        onClick={() => setCopilotOpen((s) => !s)}
        className="lg:hidden fixed bottom-16 right-5 z-40 rounded-full p-3 shadow-xl"
        style={{
          background: "radial-gradient(60% 60% at 50% 50%, #38BDF8 0%, #1E40AF 100%)",
          boxShadow: "0 0 24px rgba(56,189,248,0.5)",
        }}
        aria-label="Uplift Co-Pilot"
        title="Uplift Co-Pilot"
      >
        <RobotIcon className="w-7 h-7" />
      </button>

      {/* Mobile Co-Pilot sheet */}
      {!copilotOpen ? null : (
        <div className="lg:hidden fixed inset-x-0 bottom-14 z-40">
          <div className="mx-3 mb-3 rounded-2xl bg-[#0F172A] border border-white/10 p-4 shadow-2xl">
            <div className="flex items-center gap-2 mb-3">
              <RobotIcon className="w-6 h-6" />
              <div className="text-[#FFD700] font-semibold text-sm">Uplift Co-Pilot</div>
              <button
                className="ml-auto text-white/60 text-sm px-2 py-1 bg-white/5 rounded-lg"
                onClick={() => setCopilotOpen(false)}
              >
                Close
              </button>
            </div>
            <ul className="space-y-2 text-sm">
              <li>✅ Top 3 stalled deals</li>
              <li>📞 Leads likely to convert this week</li>
              <li>✍️ Suggested follow-up message</li>
              <li>📁 Account health snapshot</li>
            </ul>
            <input
              className="mt-3 w-full bg-[#0C1428] border border-white/10 rounded-lg px-3 py-2 text-sm placeholder:text-white/40"
              placeholder="Ask Uplift anything…"
            />
          </div>
        </div>
      )}

      {/* Mobile bottom navigation */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 h-12 bg-[#0F172A] border-t border-white/10 flex items-center justify-around z-40">
        {[
          { key: "home", label: "Home", onClick: () => setActiveBottom("home") },
          { key: "leads", label: "Leads", onClick: () => onSwitch?.("leads") },
          { key: "activities", label: "Activities", onClick: () => onSwitch?.("activity-center") },
          { key: "deals", label: "Deals", onClick: () => setActiveBottom("deals") }, // placeholder
          { key: "more", label: "More", onClick: () => setMobileMoreOpen((s) => !s) },
        ].map((b) => (
          <button
            key={b.key}
            onClick={b.onClick}
            className={`text-xs px-2 py-1 rounded ${activeBottom === b.key ? "text-[#38BDF8]" : "text-white/70"}`}
          >
            {b.label}
          </button>
        ))}
      </nav>

      {/* Mobile More drawer */}
      {mobileMoreOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileMoreOpen(false)} />
          <div className="absolute bottom-0 inset-x-0 bg-[#0C1428] border-t border-white/10 p-4 rounded-t-2xl">
            <div className="text-sm text-white/80 mb-2">More Modules</div>
            <div className="grid grid-cols-2 gap-2">
              {[
                "Opportunities / Deals",
                "Accounts",
                "Contacts",
                "Quotations",
                "Orders / Sales",
                "Payments / Invoices",
                "Inventory",
                "Tickets / Projects",
                "Workflow & Automation",
                "Campaigns / Marketing",
                "Documents / Files",
                "Reports & Analytics",
                "Integrations",
                "Company Settings",
                "Logout",
              ].map((m, i) => (
                <div key={i} className="bg-white/5 rounded-lg px-3 py-2 text-xs text-white/80">{m}</div>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              <button className="px-3 py-2 text-xs rounded-lg bg-white/10" onClick={() => setShowCompanyModal(true)}>Company Settings</button>
              <button className="px-3 py-2 text-xs rounded-lg bg-white/10" onClick={onLogout}>Logout</button>
              <button className="ml-auto px-3 py-2 text-xs rounded-lg bg-white/10" onClick={() => setMobileMoreOpen(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* 🪄 Company Onboarding Modal (kept) */}
      {showCompanyModal && (
        <OnboardingModal
          user={user}
          company={company}
          onSave={updateCompany}
          onClose={() => setShowCompanyModal(false)}
        />
      )}
    </div>
  );
}
