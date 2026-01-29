"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type User = {
  id: string;
  email: string;
  is_active: boolean;
  roles: string[];
};

export default function AdminPage() {
  const router = useRouter();

  // 🔐 auth state
  const myRoles = useAuthStore((s) => s.roles);
  const myEmail = useAuthStore((s) => s.email);
  const authReady = useAuthStore((s) => s.authReady);

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingUser, setUpdatingUser] = useState<string | null>(null);

  // Auth guard + fetch users
  useEffect(() => {
    if (!authReady) return;

    if (!myRoles.includes("admin")) {
      router.replace("/dashboard");
      return;
    }

    const fetchUsers = async () => {
      try {
        const res = await api.get("/admin/users");
        setUsers(res.data);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [authReady, myRoles, router]);

  // SINGLE ROLE TOGGLE (SAFE)

  const setRole = async (user: User, role: string) => {
    // ⛔ block self-role change (VERY IMPORTANT)
    if (user.email === myEmail) {
      alert("You cannot change your own role");
      return;
    }

    setUpdatingUser(user.id);

    try {
      // remove existing roles
      for (const r of user.roles) {
        await api.delete(`/admin/users/${user.id}/roles/${r}`);
      }

      // assign selected role
      await api.post(`/admin/users/${user.id}/roles/${role}`);

      // update UI
      setUsers((prev) =>
        prev.map((u) =>
          u.id === user.id ? { ...u, roles: [role] } : u
        )
      );
    } finally {
      setUpdatingUser(null);
    }
  };


  // Delete user

  const deleteUser = async (user: User) => {
    // ⛔ prevent self delete
    if (user.email === myEmail) {
      alert("You cannot delete your own account");
      return;
    }

    if (!confirm(`Delete user ${user.email}?`)) return;

    await api.delete(`/admin/users/${user.id}`);
    setUsers((prev) => prev.filter((u) => u.id !== user.id));
  };

  // UI guards
  if (!authReady) {
    return <div className="p-8">Checking permissions...</div>;
  }

  if (!myRoles.includes("admin")) {
    return null;
  }

  // UI
  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-semibold">Admin Dashboard</h1>

      {loading ? (
        <p className="text-gray-500">Loading users...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg bg-white shadow">
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-100">
              <tr>
                <th className="border px-4 py-3 text-left">Email</th>
                <th className="border px-4 py-3 text-left">Role</th>
                <th className="border px-4 py-3 text-center">Status</th>
                <th className="border px-4 py-3 text-center">Delete</th>
              </tr>
            </thead>

            <tbody>
              {users.map((u) => {
                const isSelf = u.email === myEmail;

                return (
                  <tr key={u.id} className="hover:bg-gray-50">
                    {/* EMAIL */}
                    <td className="border px-4 py-3">{u.email}</td>

                    {/* ROLE TOGGLE */}
                    <td className="border px-4 py-3">
                      <div className="flex gap-2">
                        {["user", "admin"].map((role) => {
                          const active = u.roles.includes(role);

                          return (
                            <button
                              key={role}
                              onClick={() => setRole(u, role)}
                              disabled={updatingUser === u.id || isSelf}
                              title={
                                isSelf
                                  ? "You cannot change your own role"
                                  : ""
                              }
                              className={`rounded px-3 py-1 text-sm font-medium transition ${active
                                  ? "bg-blue-600 text-white"
                                  : "bg-gray-100 text-gray-600"
                                } disabled:opacity-50`}
                            >
                              {role}
                            </button>
                          );
                        })}
                      </div>
                    </td>

                    {/* STATUS */}
                    <td className="border px-4 py-3 text-center">
                      {u.is_active ? (
                        <span className="rounded bg-green-100 px-2 py-1 text-sm text-green-700">
                          Active
                        </span>
                      ) : (
                        <span className="rounded bg-red-100 px-2 py-1 text-sm text-red-700">
                          Inactive
                        </span>
                      )}
                    </td>

                    {/* DELETE */}
                    <td className="border px-4 py-3 text-center">
                      <button
                        onClick={() => deleteUser(u)}
                        disabled={isSelf}
                        title={
                          isSelf
                            ? "You cannot delete your own account"
                            : ""
                        }
                        className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
