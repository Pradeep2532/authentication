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

export const useAuthStore = create<AuthState>((set: any) => ({
  accessToken: null,
  roles: [],
  email: null,
  authReady: false,

  setToken: (token: any) => set({ accessToken: token }),
  setRoles: (roles: any) => set({ roles }),
  setEmail: (email: any) => set({ email }),   
  setAuthReady: () => set({ authReady: true }),

  logout: () =>
    set({
      accessToken: null,
      roles: [],
      email: null,
      authReady: true,
    }),
}));
