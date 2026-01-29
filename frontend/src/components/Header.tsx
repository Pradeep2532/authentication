"use client";

import { useLogout } from "@/lib/useLogout";

export default function Header() {
  const logout = useLogout();

  return (
    <header className="flex items-center justify-between p-4 border-b">
      <h1 className="text-lg font-semibold">My App</h1>

      <button
        onClick={logout}
        className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
      >
        Logout
      </button>
    </header>
  );
}
