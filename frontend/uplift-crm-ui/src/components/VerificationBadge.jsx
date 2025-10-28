export default function VerificationBadge({ verified }) {
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full ${verified ? "bg-yellow-400/20 text-yellow-300 border border-yellow-400/40" : "bg-slate-500/20 text-slate-300 border border-slate-500/40"}`}>
      {verified ? "Verified" : "Unverified"}
    </span>
  );
}
