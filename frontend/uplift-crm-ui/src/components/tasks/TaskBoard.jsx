import TaskCard from "./TaskCard";
export default function TaskBoard({ tasks, onComplete }) {
  const col = (label, filterFn) => (
    <div className="flex-1 space-y-3">
      <div className="text-slate-200 mb-2">{label}</div>
      {tasks.filter(filterFn).map(t => <TaskCard key={t.id} t={t} onComplete={onComplete} />)}
    </div>
  );
  return (
    <div className="grid md:grid-cols-4 gap-4">
      {col("Today", t => t.status === "Pending")}
      {col("Upcoming", t => t.status === "Planned")}
      {col("Overdue", t => t.status === "Overdue")}
      {col("Completed", t => t.status === "Completed")}
    </div>
  );
}
