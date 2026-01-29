"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const storeSetRoles = useAuthStore((s) => s.setRoles);
  const storeSetEmail = useAuthStore((s) => s.setEmail);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setError(null);

    if (!email || !password) {
      setError("Email and password are required");
      return;
    }

    try {
      setLoading(true);

      const res = await api.post("/auth/login", {
        email,
        password,
      });

      // Set the token first
      setToken(res.data.access_token);

      // Fetch user info to get roles
      try {
        const meRes = await api.get("/protected/me");
        storeSetRoles(meRes.data.roles);
        storeSetEmail(meRes.data.email);

        // Redirect to appropriate page based on role
        if (meRes.data.roles.includes("admin")) {
          router.push("/admin");
        } else {
          router.push("/dashboard");
        }
      } catch (err) {
        console.error("Failed to fetch user info", err);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || "Invalid email or password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        <h1 className="mb-6 text-center text-2xl font-semibold">
          Login to your account
        </h1>

        {error && (
          <div className="mb-4 rounded bg-red-100 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="space-y-4 ">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
           className="w-full"/>

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
           className="w-full"/>

          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-black text-white hover:bg-gray-900"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-gray-600">
          Don’t have an account?{" "}
          <a href="/signup" className="font-medium">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
}
