export default function TaskCard({ t, onComplete }) {
  return (
    <div className="rounded-2xl p-4 bg-white/5 border border-white/10">
      <div className="text-white font-medium">{t.title}</div>
      <div className="text-sm text-slate-300 mt-1">{t.type} • due {t.due_date ? new Date(t.due_date).toLocaleString() : "—"}</div>
      <div className="mt-3 flex gap-2">
        <button onClick={() => onComplete(t.id, "Follow-Up Needed")} className="px-3 py-1 rounded-lg bg-yellow-400/20 text-yellow-300 border border-yellow-400/40">Mark Done</button>
      </div>
    </div>
  );
}
