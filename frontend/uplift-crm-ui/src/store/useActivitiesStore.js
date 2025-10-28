import { create } from "zustand";
import * as api from "../api/activities";

export const useActivitiesStore = create((set, get) => ({
  activities: [],
  tasks: [],
  loading: false,
  summary: null,

  fetchActivities: async (filters = {}) => {
    set({ loading: true });
    const data = await api.listActivities(filters);
    // split into tasks vs completed activities (UI views)
    set({
      activities: data.filter(a => a.status === "Completed" || a.status === "Cancelled"),
      tasks: data.filter(a => ["Planned","Pending","Overdue"].includes(a.status)),
      loading: false
    });
  },

  completeTask: async (taskId, outcome) => {
    const updated = await api.updateActivity(taskId, { status: "Completed", outcome });
    // refetch to get auto-generated next task as well
    await get().fetchActivities();
    return updated;
  },

  addActivity: async (payload) => {
    const a = await api.createActivity(payload);
    await get().fetchActivities();
    return a;
  },

  verifyActivity: async (payload) => {
    const a = await api.verifyActivity(payload);
    await get().fetchActivities();
    return a;
  },

  loadSummary: async () => {
    const s = await api.summaryOverview();
    set({ summary: s });
  }
}));
