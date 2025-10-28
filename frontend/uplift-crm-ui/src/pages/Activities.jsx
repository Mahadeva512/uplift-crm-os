import { useEffect } from "react";
import { useActivitiesStore } from "../store/useActivitiesStore";
import ActivityCard from "../components/activities/ActivityCard";

export default function Activities() {
  const { activities, fetchActivities, loading } = useActivitiesStore();

  useEffect(() => { fetchActivities({}); }, [fetchActivities]);

  return (
    <div className="p-6 min-h-screen bg-[#0C1428]">
      <div className="text-white text-2xl font-semibold mb-4">Activities</div>
      {loading && <div className="text-slate-300">Loading…</div>}
      <div className="space-y-3">
        {activities.map(a => <ActivityCard key={a.id} a={a} onClick={() => { /* open drawer */ }} />)}
      </div>
    </div>
  );
}
