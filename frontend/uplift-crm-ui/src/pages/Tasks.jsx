import { useEffect } from "react";
import { useActivitiesStore } from "../store/useActivitiesStore";
import TaskBoard from "../components/tasks/TaskBoard";

export default function Tasks() {
  const { tasks, fetchActivities, completeTask } = useActivitiesStore();
  useEffect(() => { fetchActivities({}); }, [fetchActivities]);

  return (
    <div className="p-6 min-h-screen bg-[#0C1428]">
      <div className="text-white text-2xl font-semibold mb-4">Tasks</div>
      <TaskBoard tasks={tasks} onComplete={(id, outcome) => completeTask(id, outcome)} />
    </div>
  );
}
