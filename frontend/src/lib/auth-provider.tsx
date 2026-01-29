"use client";

import { useEffect } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const setToken = useAuthStore((s:any) => s.setToken);
  const setRoles = useAuthStore((s: any) => s.setRoles);
  const setAuthReady = useAuthStore((s: any) => s.setAuthReady);
  const setEmail = useAuthStore((s: any) => s.setEmail);
  const logout = useAuthStore((s: any) => s.logout);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const refreshRes = await api.post("/auth/refresh");
        setToken(refreshRes.data.access_token);

        const meRes = await api.get("/protected/me");
        setRoles(meRes.data.roles);
        setEmail(meRes.data.email);   // 🔥 MUST

      } catch {
        logout();
      } finally {
        // 🔑 VERY IMPORTANT
        setAuthReady();
      }
    };

    initAuth();
  }, []);

  return <>{children}</>;
}
