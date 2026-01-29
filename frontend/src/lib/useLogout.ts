"use client";

import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export const useLogout = () => {
  const router = useRouter();
  const logoutStore = useAuthStore((s:any) => s.logout);

  const logout = async () => {
    try {
      // 🔥 call backend logout
      await api.post("/auth/logout");
    } catch (err) {
      // ignore errors (token may already be expired)
      console.warn("Logout request failed, continuing");
    } finally {
      // 🔥 clear frontend auth state
      logoutStore();

      // 🔥 redirect to login
      router.replace("/login");
    }
  };

  return logout;
};
