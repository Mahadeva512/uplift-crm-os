import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-hot-toast";
import botImg from "@/assets/ai-bot.png";

export default function CopilotHeader({
  activities = [],
  insights = {},
  onSummarizeAll,
  onSuggestBulk,
  aiPopMsg,
  thinking,
}) {
  const [blink, setBlink] = useState(false);
  const blinkRef = useRef(null);

  useEffect(() => {
    blinkRef.current = setInterval(() => setBlink((b) => !b), 5000);
    return () => clearInterval(blinkRef.current);
  }, []);

  useEffect(() => {
    if (aiPopMsg) toast.success(aiPopMsg, { duration: 3000 });
  }, [aiPopMsg]);

  const total = activities?.length || 0;
  const positive = insights?.sentiment?.Positive || 0;

  // ✅ injected dynamic label logic
  const label = insights?.scope === "tasks" ? "tasks" : "activities";

  const tone =
    insights?.toneText ||
    (total
      ? `Out of ${total} ${label} this week, you’ve completed most. Keep compounding 🔥`
      : `I’m ready to assist with your first ${label}!`);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative rounded-3xl border border-white/10 bg-[#0B1330]/80 backdrop-blur-xl p-5 sm:p-6 shadow-[0_0_30px_rgba(0,72,232,0.2)] overflow-hidden"
    >
      <div
        className="absolute inset-0 pointer-events-none opacity-40 blur-3xl"
        style={{
          background:
            "radial-gradient(900px 300px at 70% -10%, rgba(0,132,255,.25), transparent)",
        }}
      />

      <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <motion.div
            animate={{ rotate: thinking ? [0, 8, -8, 0] : [0, 2, -2, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="relative w-20 h-20 sm:w-24 sm:h-24 flex items-center justify-center"
          >
            <div className="absolute -inset-6 rounded-full bg-gradient-to-tr from-cyan-400/40 via-blue-400/30 to-transparent blur-3xl animate-pulse" />
            <div className="relative rounded-full overflow-hidden border border-cyan-300/40 shadow-[0_0_25px_rgba(34,211,238,0.4)] bg-gradient-to-b from-[#091C2F] to-[#060C20]">
              <img
                src={botImg}
                alt="AI Copilot"
                className={`w-20 h-20 sm:w-24 sm:h-24 object-contain transition-all duration-500 ${
                  thinking ? "brightness-125 scale-110" : ""
                }`}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-transparent via-transparent to-cyan-400/10" />
            </div>
            {blink && !thinking && (
              <div className="absolute w-3 h-3 bg-cyan-300/80 rounded-full blur-[1px] opacity-80 animate-pulse" />
            )}
            <AnimatePresence>
              {thinking && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: -10 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="absolute -right-1 -top-1 text-[10px] px-2 py-1 rounded-full bg-cyan-400/20 border border-cyan-300/30 text-cyan-200 shadow-[0_0_10px_rgba(34,211,238,0.4)]"
                >
                  Thinking…
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          <div>
            <div className="text-slate-100 font-semibold text-base">AI Copilot</div>
            <div className="text-xs text-slate-400">
              Watching <b>{total}</b> {label} · <b>{positive}</b> positive interactions
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onSummarizeAll}
            className="text-xs px-3 py-1.5 rounded-full bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-100 active:scale-95"
          >
            Summarize All
          </button>
          <button
            onClick={onSuggestBulk}
            className="text-xs px-3 py-1.5 rounded-full bg-yellow-400 text-slate-900 hover:bg-yellow-300 active:scale-95"
          >
            Plan Next Steps
          </button>
        </div>
      </div>

      <div className="mt-4 sm:mt-5 bg-[#0E1A35]/80 border border-slate-600/40 rounded-2xl p-4 text-sm text-slate-200 backdrop-blur-md shadow-[0_0_25px_rgba(0,0,0,0.4)]">
        <p className="leading-relaxed">{tone}</p>
      </div>
    </motion.div>
  );
}
