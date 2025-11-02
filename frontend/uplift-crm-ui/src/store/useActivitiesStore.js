// src/store/useActivitiesStore.js
import { create } from "zustand";
import apiClient from "@/api/apiClient";

export const useActivitiesStore = create((set, get) => ({
  activities: [],
  tasks: [],
  loading: false,
  summary: null,

  fetchActivities: async (filters = {}) => {
    try {
      set({ loading: true });
      const { data } = await apiClient.get("/activities", { params: filters });
      set({
        activities: data.filter((a) => a.status === "Completed" || a.status === "Cancelled"),
        tasks: data.filter((a) => ["Planned", "Pending", "Overdue"].includes(a.status)),
        loading: false,
      });
    } catch (err) {
      console.error("Failed to fetch activities:", err);
      set({ loading: false });
    }
  },

  completeTask: async (taskId, outcome) => {
    const { data } = await apiClient.patch(`/activities/${taskId}`, {
      status: "Completed",
      outcome,
    });
    await get().fetchActivities();
    return data;
  },

  addActivity: async (payload) => {
    const { data } = await apiClient.post("/activities", payload);
    await get().fetchActivities();
    return data;
  },

  verifyActivity: async (payload) => {
    const { data } = await apiClient.post("/activities/verify", payload);
    await get().fetchActivities();
    return data;
  },

  loadSummary: async () => {
    const { data } = await apiClient.get("/activities/summary");
    set({ summary: data });
  },
}));
