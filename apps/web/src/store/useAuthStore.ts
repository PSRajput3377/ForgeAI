/**
 * Auth state (Zustand) — holds the JWT token pair and current user.
 * Tokens persist to localStorage so a refresh keeps the session.
 */
import { create } from "zustand";

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setSession: (access: string, refresh: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

const ACCESS_KEY = "forge.access";
const REFRESH_KEY = "forge.refresh";

function read(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: read(ACCESS_KEY),
  refreshToken: read(REFRESH_KEY),
  user: null,
  setSession: (access, refresh) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACCESS_KEY, access);
      window.localStorage.setItem(REFRESH_KEY, refresh);
    }
    set({ accessToken: access, refreshToken: refresh });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(ACCESS_KEY);
      window.localStorage.removeItem(REFRESH_KEY);
    }
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));
