import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function OnboardingModal({ user, company, onSave }) {
  const [open, setOpen] = useState(
    company?.company_name?.endsWith("’s Company") ||
      company?.company_name?.endsWith("'s Company")
  );
  const [form, setForm] = useState({
    company_name: company?.company_name || "",
    industry: company?.industry || "",
    team_size: company?.team_size || "",
  });
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(form);
      setOpen(false);
    } catch (err) {
      alert("Could not update company. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-[#141C2F] text-white rounded-2xl p-8 w-[95%] max-w-md border border-white/10 shadow-2xl"
          >
            <h2 className="text-2xl font-bold mb-2">
              Welcome, {user?.full_name?.split(" ")[0]} 👋
            </h2>
            <p className="text-slate-400 mb-6 text-sm">
              Let’s set up your company before we dive in.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm mb-1">Company Name</label>
                <input
                  type="text"
                  value={form.company_name}
                  onChange={(e) =>
                    setForm({ ...form, company_name: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-md bg-white/5 border border-white/10 focus:border-yellow-400 outline-none text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Industry</label>
                <input
                  type="text"
                  value={form.industry}
                  onChange={(e) =>
                    setForm({ ...form, industry: e.target.value })
                  }
                  placeholder="e.g. Retail, Manufacturing, Services"
                  className="w-full px-3 py-2 rounded-md bg-white/5 border border-white/10 focus:border-yellow-400 outline-none text-sm"
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Team Size</label>
                <input
                  type="number"
                  min="1"
                  value={form.team_size}
                  onChange={(e) =>
                    setForm({ ...form, team_size: e.target.value })
                  }
                  placeholder="e.g. 10"
                  className="w-full px-3 py-2 rounded-md bg-white/5 border border-white/10 focus:border-yellow-400 outline-none text-sm"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 bg-yellow-400 text-black font-semibold rounded-lg hover:bg-yellow-300 transition disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save & Continue"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
