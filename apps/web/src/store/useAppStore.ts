/**
 * Global client state (Zustand). Seeded minimally in Phase 1; real slices
 * (auth, active project, agent run state) are added in later phases.
 */
import { create } from "zustand";

interface AppState {
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeProjectId: null,
  setActiveProjectId: (id) => set({ activeProjectId: id }),
}));
