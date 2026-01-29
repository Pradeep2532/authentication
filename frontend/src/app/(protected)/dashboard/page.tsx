"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const [me, setMe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const token = useAuthStore((s) => s.accessToken);
  const roles = useAuthStore((s) => s.roles);
  const router = useRouter();
  const authReady = useAuthStore((s) => s.authReady);

  useEffect(() => {
    // Wait until auth is ready
    if (!authReady) return;

    // If user is admin, redirect to admin page
    if (roles.includes("admin")) {
      router.replace("/admin");
      return;
    }

    // Fetch user info for regular users
    const fetchMe = async () => {
      try {
        const res = await api.get("/protected/me");
        setMe(res.data);
      } catch (err) {
        console.error("Failed to fetch user info", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMe();
  }, [authReady, roles, router]);

  return (
    <div className="p-10">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {me && <p className="mt-4">Welcome, {me.email}</p>}
    </div>
  );
}
