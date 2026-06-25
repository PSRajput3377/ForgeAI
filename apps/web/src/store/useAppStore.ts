/**
 * Global client state (Zustand). Holds the active project + workspace so the
 * workspace screen knows which project a run targets (Phase 13.4). Persisted to
 * localStorage so a refresh keeps you in the same project.
 */
import { create } from "zustand";

const PROJECT_ID = "forge.project.id";
const PROJECT_NAME = "forge.project.name";
const WORKSPACE_ID = "forge.workspace.id";

function read(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function write(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  if (value === null) window.localStorage.removeItem(key);
  else window.localStorage.setItem(key, value);
}

interface AppState {
  activeProjectId: string | null;
  activeProjectName: string | null;
  workspaceId: string | null;
  setActiveProject: (id: string | null, name: string | null) => void;
  setWorkspaceId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeProjectId: read(PROJECT_ID),
  activeProjectName: read(PROJECT_NAME),
  workspaceId: read(WORKSPACE_ID),
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
