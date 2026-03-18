"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCollection, getStats, deleteRecord } from "@/lib/api";
import type { CollectionItem, CollectionStats } from "@/lib/types";
import { useStore } from "@/lib/store";
import Link from "next/link";

export default function CollectionPage() {
  const [collection, setCollection] = useState<CollectionItem[]>([]);
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const { isLoggedIn, loadAuth } = useStore();
  const router = useRouter();

  useEffect(() => {
    loadAuth();
  }, [loadAuth]);

  useEffect(() => {
    // Wait for auth check, then redirect or fetch
    if (!isLoggedIn && typeof window !== "undefined" && !localStorage.getItem("crate_token")) {
      setLoading(false);
      return;
    }

    Promise.all([getCollection(), getStats()])
      .then(([col, st]) => {
        setCollection(col);
        setStats(st);
      })
      .catch(() => {
        // Auth failed — clear and show landing
        setCollection([]);
        setStats(null);
      })
      .finally(() => setLoading(false));
  }, [isLoggedIn]);

  if (loading) {
    return <p className="text-crate-muted">Loading...</p>;
  }

  // Not logged in — show landing
  if (!isLoggedIn) {
    return (
      <div className="text-center py-24">
        <h1 className="text-4xl font-bold mb-3">Crate</h1>
        <p className="text-lg text-crate-muted mb-2">
          A collectively-built map of music history.
        </p>
        <p className="text-sm text-crate-muted mb-8 max-w-md mx-auto">
          Build a knowledge graph of your vinyl collection. Connect with friends.
          Discover how music scenes formed, genres migrated, and sounds evolved.
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            href="/register"
            className="px-6 py-2.5 bg-crate-accent text-black font-medium rounded hover:bg-amber-400 transition-colors"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="px-6 py-2.5 border border-crate-border rounded hover:border-crate-accent transition-colors"
          >
            Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Your Collection</h1>
          {stats && (
            <p className="text-sm text-crate-muted mt-1">
              {stats.total_albums} albums &middot; {stats.total_artists} artists &middot;{" "}
              {stats.total_labels} labels &middot; {stats.total_genres} genres
            </p>
          )}
        </div>
        <Link
          href="/add"
          className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 transition-colors"
        >
          + Add Record
        </Link>
      </div>

      {collection.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-crate-muted text-lg">No records yet.</p>
          <p className="text-crate-muted text-sm mt-2">
            <Link href="/add" className="text-crate-accent hover:underline">
              Add your first record
            </Link>{" "}
            or import your Discogs collection.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {collection.map((item) => (
            <div
              key={item.discogs_id}
              className="border border-crate-border rounded-lg p-4 hover:border-crate-accent transition-colors bg-crate-surface relative group"
            >
              <Link href={`/record/${item.discogs_id}`}>
                <p className="font-medium truncate">{item.title}</p>
                <p className="text-sm text-crate-muted truncate">
                  {item.artists.join(", ")}
                </p>
                <p className="text-xs text-crate-muted mt-1">{item.year || "Unknown year"}</p>
              </Link>
              <button
                onClick={async (e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (!confirm(`Remove "${item.title}" from your collection?`)) return;
                  try {
                    await deleteRecord(item.discogs_id);
                    setCollection((prev) => prev.filter((c) => c.discogs_id !== item.discogs_id));
                    if (stats) setStats({ ...stats, total_albums: stats.total_albums - 1 });
                  } catch (err) {
                    console.error(err);
                  }
                }}
                className="absolute top-2 right-2 text-crate-muted hover:text-red-400 text-lg leading-none px-1"
                title="Remove from collection"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
