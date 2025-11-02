// src/store/useAuthStore.js
import { create } from "zustand";

export const useAuthStore = create((set, get) => ({
  user: null,
  setUser: (user) => {
    set({ user });
    // Expose current user email for apiClient interceptor
    if (typeof window !== "undefined") {
      window.__upliftGetUserEmail__ = () => user?.email || null;
    }
  },
  logout: () => {
    set({ user: null });
    if (typeof window !== "undefined") {
      window.__upliftGetUserEmail__ = null;
    }
  },
}));
