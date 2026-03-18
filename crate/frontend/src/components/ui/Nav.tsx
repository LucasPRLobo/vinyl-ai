"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";

export default function Nav() {
  const { isLoggedIn, userName, logout, loadAuth } = useStore();

  useEffect(() => {
    loadAuth();
  }, [loadAuth]);

  // Pre-alpha: core features only
  const links = isLoggedIn
    ? [
        { href: "/", label: "Collection" },
        { href: "/add", label: "Add" },
        { href: "/graph", label: "Graph" },
        { href: "/feed", label: "Feed" },
        { href: "/groups", label: "Groups" },
      ]
    : [];

  return (
    <nav className="border-b border-crate-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-8">
        <Link href="/" className="text-crate-accent font-bold text-lg tracking-tight">
          Crate
        </Link>
        <div className="flex gap-5">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-crate-muted hover:text-crate-text transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {isLoggedIn ? (
          <>
            <span className="text-sm text-crate-muted">{userName}</span>
            <button
              onClick={logout}
              className="text-sm text-crate-muted hover:text-crate-text transition-colors"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link
              href="/login"
              className="text-sm text-crate-muted hover:text-crate-text transition-colors"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="text-sm px-3 py-1 bg-crate-accent text-black rounded hover:bg-amber-400 transition-colors"
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
