// src/context/AICopilotContext.jsx
import React, { createContext, useContext, useState, useEffect } from "react";
import { useAI } from "@/hooks/useAI";

const AICopilotContext = createContext();

export function AICopilotProvider({ children }) {
  const ai = useAI();
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function refreshInsights() {
    try {
      setLoading(true);
      const data = await ai.getInsights({ days: 7 });
      setInsights(data || []);
    } catch (err) {
      console.error("AICopilot: insights error", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshInsights();
  }, []);

  const value = {
    ai,
    insights,
    loading,
    error,
    refreshInsights,
    setInsights,
  };

  return (
    <AICopilotContext.Provider value={value}>
      {children}
    </AICopilotContext.Provider>
  );
}

// ✅ Exported hook used in Leads.jsx
export const useAICopilot = () => useContext(AICopilotContext);
