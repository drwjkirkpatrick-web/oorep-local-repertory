"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [setup, setSetup] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/admin/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, setup }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Login failed");
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-sm mx-auto px-6 py-20">
      <h1 className="text-2xl font-bold mb-6 text-center">Admin Login</h1>
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4"><p className="text-red-700 text-sm">{error}</p></div>}
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="flex items-center gap-2">
          <input id="setup" type="checkbox" checked={setup} onChange={(e) => setSetup(e.target.checked)} />
          <label htmlFor="setup" className="text-sm text-gray-600">First-time setup</label>
        </div>
        <button type="submit" disabled={loading} className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50">{loading ? "Loading..." : "Login"}</button>
      </form>
    </main>
  );
}
