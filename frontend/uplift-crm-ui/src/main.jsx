// main.jsx — Uplift CRM OS (Global AI Copilot Context Enabled)
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { AICopilotProvider } from "@/context/AICopilotContext"; // ✅ Global AI Context Provider

createRoot(document.getElementById("root")).render(
  <StrictMode>
    {/* ✅ Wrap the entire app inside AI Copilot Provider */}
    <AICopilotProvider>
      <App />
    </AICopilotProvider>
  </StrictMode>
);
