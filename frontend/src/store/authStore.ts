import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  roles: string[];
  email: string | null;
  authReady: boolean;

  setToken: (token: string) => void;
  setRoles: (roles: string[]) => void;
  setEmail: (email: string) => void;
  setAuthReady: () => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  roles: [],
  email: null,
  authReady: false,

  setToken: (token) => set({ accessToken: token }),
  setRoles: (roles) => set({ roles }),
  setEmail: (email) => set({ email }),   // ✅ FIX
  setAuthReady: () => set({ authReady: true }),

  logout: () =>
    set({
      accessToken: null,
      roles: [],
      email: null,
      authReady: true,
    }),
}));
