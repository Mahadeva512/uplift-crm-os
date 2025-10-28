import VerificationBadge from "../shared/VerificationBadge";

export default function ActivityCard({ a, onClick }) {
  return (
    <div onClick={onClick} className="rounded-2xl p-4 bg-white/5 border border-white/10 hover:border-yellow-400/40 transition cursor-pointer">
      <div className="flex items-center justify-between">
        <div className="text-white font-medium">{a.title}</div>
        <VerificationBadge verified={a.verified_event} />
      </div>
      <div className="mt-1 text-sm text-slate-300">{a.type} • {a.outcome || a.status}</div>
      <div className="mt-1 text-xs text-slate-400">
        {new Date(a.created_at).toLocaleString()}
        {a.call_duration ? ` • ${Math.round(a.call_duration/60)} min` : ""}
      </div>
    </div>
  );
}
