"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register as registerApi } from "@/lib/api";
import { useStore } from "@/lib/store";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const storeLogin = useStore((s) => s.login);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await registerApi(email, name, password);
      storeLogin(res.token, res.user_id, res.name);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20">
      <h1 className="text-2xl font-bold mb-6">Create Account</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text" placeholder="Name" value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        <input
          type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        <input
          type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit" disabled={loading}
          className="w-full px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Create Account"}
        </button>
      </form>
      <p className="text-sm text-crate-muted mt-4">
        Have an account? <Link href="/login" className="text-crate-accent hover:underline">Login</Link>
      </p>
    </div>
  );
}
