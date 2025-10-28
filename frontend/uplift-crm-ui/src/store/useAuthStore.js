// src/store/useAuthStore.js
import { create } from "zustand";

// ✅ Simple global auth state
export const useAuthStore = create((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
}));
