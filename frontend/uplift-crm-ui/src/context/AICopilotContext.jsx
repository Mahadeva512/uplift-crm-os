// src/context/AICopilotContext.jsx
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useAI } from "@/hooks/useAI";

const AICopilotCtx = createContext(null);

export function AICopilotProvider({ children, defaultDays = 7 }) {
  const { getInsights, summarizeActivity, suggestNextStep, getWeeklyReport, ping } = useAI();
  const [days, setDays] = useState(defaultDays);
  const [userId, setUserId] = useState("");
  const [leadId, setLeadId] = useState("");
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [healthy, setHealthy] = useState("checking");

  const refreshInsights = async () => {
    setLoading(true);
    try {
      const data = await getInsights({ days, user_id: userId, lead_id: leadId });
      setInsights(data);
      setHealthy("ok");
    } catch (e) {
      console.warn("AICopilot: insights error", e.message);
      setHealthy("down");
    } finally {
      setLoading(false);
    }
  };

  // health on mount
  useEffect(() => {
    (async () => {
      try { await ping(); setHealthy("ok"); } catch { setHealthy("down"); }
    })();
  }, []);

  // refresh on filters
  useEffect(() => { refreshInsights(); }, [days, userId, leadId]);

  // poll every 60s
  useEffect(() => {
    const id = setInterval(refreshInsights, 60_000);
    return () => clearInterval(id);
  }, [days, userId, leadId]);

  const value = useMemo(() => ({
    days, setDays,
    userId, setUserId,
    leadId, setLeadId,
    insights, loading, healthy,
    actions: { summarizeActivity, suggestNextStep, getWeeklyReport, refreshInsights },
  }), [days, userId, leadId, insights, loading, healthy]);

  return <AICopilotCtx.Provider value={value}>{children}</AICopilotCtx.Provider>;
}

export function useAICopilot() {
  const ctx = useContext(AICopilotCtx);
  if (!ctx) throw new Error("useAICopilot must be used within <AICopilotProvider>");
  return ctx;
}
