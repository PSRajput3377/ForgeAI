/**
 * Global client state (Zustand). Holds the active project + workspace so the
 * workspace screen knows which project a run targets (Phase 13.4). Persisted to
 * localStorage so a refresh keeps you in the same project.
 *
 * SSR-safe: initial state is always null (matching the server render). Values
 * are read from localStorage only after mount via hydrate(), so the first client
 * render matches the server and there is no hydration mismatch.
 */
import { useEffect } from "react";
import { create } from "zustand";

const PROJECT_ID = "forge.project.id";
const PROJECT_NAME = "forge.project.name";
const WORKSPACE_ID = "forge.workspace.id";

function write(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  if (value === null) window.localStorage.removeItem(key);
  else window.localStorage.setItem(key, value);
}

interface AppState {
  hydrated: boolean;
  activeProjectId: string | null;
  activeProjectName: string | null;
  workspaceId: string | null;
  hydrate: () => void;
  setActiveProject: (id: string | null, name: string | null) => void;
  setWorkspaceId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  hydrated: false,
  activeProjectId: null,
  activeProjectName: null,
  workspaceId: null,
  hydrate: () => {
    if (typeof window === "undefined") return;
    set({
      hydrated: true,
      activeProjectId: window.localStorage.getItem(PROJECT_ID),
      activeProjectName: window.localStorage.getItem(PROJECT_NAME),
      workspaceId: window.localStorage.getItem(WORKSPACE_ID),
    });
  },
  setActiveProject: (id, name) => {
    write(PROJECT_ID, id);
    write(PROJECT_NAME, name);
    set({ activeProjectId: id, activeProjectName: name });
  },
  setWorkspaceId: (id) => {
    write(WORKSPACE_ID, id);
    set({ workspaceId: id });
  },
}));

/** Hydrate the store from localStorage once, after mount. Returns the hydrated
 *  flag so a component can wait before acting on persisted values. */
export function useHydratedStore(): boolean {
  const hydrated = useAppStore((s) => s.hydrated);
  useEffect(() => {
    if (!hydrated) useAppStore.getState().hydrate();
  }, [hydrated]);
  return hydrated;
}
