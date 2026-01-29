"use client";

import { useEffect } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const setToken = useAuthStore((s) => s.setToken);
  const setRoles = useAuthStore((s) => s.setRoles);
  const setAuthReady = useAuthStore((s) => s.setAuthReady);
  const setEmail = useAuthStore((s) => s.setEmail);
  const logout = useAuthStore((s) => s.logout);

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
