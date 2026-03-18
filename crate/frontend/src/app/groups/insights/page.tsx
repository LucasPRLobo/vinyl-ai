"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("crate_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

interface GroupStats {
  total_albums: number;
  total_artists: number;
  total_labels: number;
  total_genres: number;
  total_members: number;
  genres: string[];
}

interface Overlap {
  title: string;
  discogs_id: number;
  owners: string[];
  owner_count: number;
}

interface SharedArtist {
  artist: string;
  albums: string[];
  album_count: number;
}

interface Bridge {
  member: string;
  unique_genres: string[];
  total_genres: number;
}

export default function GroupInsightsPage() {
  const searchParams = useSearchParams();
  const groupId = searchParams.get("id");

  const [stats, setStats] = useState<GroupStats | null>(null);
  const [overlap, setOverlap] = useState<Overlap[]>([]);
  const [bridges, setBridges] = useState<Bridge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!groupId) return;
    const headers = getAuthHeaders();

    Promise.all([
      fetch(`${API_BASE}/groups/${groupId}/insights/stats`, { headers }).then(r => r.json()),
      fetch(`${API_BASE}/groups/${groupId}/insights/overlap`, { headers }).then(r => r.json()),
      fetch(`${API_BASE}/groups/${groupId}/insights/bridges`, { headers }).then(r => r.json()),
    ])
      .then(([s, o, b]) => {
        setStats(s);
        setOverlap(o);
        setBridges(b);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [groupId]);

  if (!groupId) {
    return (
      <div className="text-center py-20">
        <p className="text-crate-muted">No group selected.</p>
        <Link href="/groups" className="text-crate-accent hover:underline text-sm">Go to Groups</Link>
      </div>
    );
  }

  if (loading) return <p className="text-crate-muted">Loading insights...</p>;

  return (
    <div className="max-w-2xl">
      <Link href="/groups" className="text-sm text-crate-muted hover:text-crate-text">
        &larr; Back to Groups
      </Link>
      <h1 className="text-2xl font-bold mt-4 mb-6">What Connects Us?</h1>

      {/* Group stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <div className="border border-crate-border rounded-lg p-3 bg-crate-surface text-center">
            <p className="text-2xl font-bold text-crate-accent">{stats.total_members}</p>
            <p className="text-xs text-crate-muted">Members</p>
          </div>
          <div className="border border-crate-border rounded-lg p-3 bg-crate-surface text-center">
            <p className="text-2xl font-bold text-crate-accent">{stats.total_albums}</p>
            <p className="text-xs text-crate-muted">Albums</p>
          </div>
          <div className="border border-crate-border rounded-lg p-3 bg-crate-surface text-center">
            <p className="text-2xl font-bold text-crate-accent">{stats.total_artists}</p>
            <p className="text-xs text-crate-muted">Artists</p>
          </div>
          <div className="border border-crate-border rounded-lg p-3 bg-crate-surface text-center">
            <p className="text-2xl font-bold text-crate-accent">{stats.total_genres}</p>
            <p className="text-xs text-crate-muted">Genres</p>
          </div>
        </div>
      )}

      {/* Shared albums */}
      <div className="mb-8">
        <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">
          Shared Albums ({overlap.length})
        </h2>
        {overlap.length === 0 ? (
          <p className="text-sm text-crate-muted">No albums owned by multiple members yet.</p>
        ) : (
          <div className="space-y-2">
            {overlap.map((o, i) => (
              <div key={i} className="flex items-center justify-between border border-crate-border rounded px-3 py-2 bg-crate-surface">
                <div>
                  <Link href={`/record/${o.discogs_id}`} className="text-sm font-medium hover:text-crate-accent">
                    {o.title}
                  </Link>
                  <p className="text-xs text-crate-muted">{o.owners.join(", ")}</p>
                </div>
                <span className="text-xs px-2 py-0.5 rounded bg-crate-accent/20 text-crate-accent">
                  {o.owner_count} owners
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bridges */}
      <div className="mb-8">
        <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">
          Bridges
        </h2>
        <p className="text-xs text-crate-muted mb-3">
          Members who are the only one covering certain genres — they bridge different parts of the group's music map.
        </p>
        {bridges.length === 0 ? (
          <p className="text-sm text-crate-muted">Not enough data yet.</p>
        ) : (
          <div className="space-y-2">
            {bridges.map((b, i) => (
              <div key={i} className="border border-crate-border rounded px-3 py-2 bg-crate-surface">
                <p className="text-sm font-medium">{b.member}</p>
                <p className="text-xs text-crate-muted">
                  Uniquely covers: {b.unique_genres.join(", ")}
                </p>
                <p className="text-xs text-crate-muted">
                  {b.total_genres} genres total
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Genres */}
      {stats && stats.genres.length > 0 && (
        <div>
          <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">
            Group Genres
          </h2>
          <div className="flex flex-wrap gap-2">
            {stats.genres.map((g, i) => (
              <span key={i} className="text-xs px-2 py-1 rounded border border-crate-border">
                {g}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Link to group graph */}
      <div className="mt-8 pt-6 border-t border-crate-border">
        <Link
          href={`/groups/graph?id=${groupId}`}
          className="text-sm text-crate-accent hover:underline"
        >
          View group graph →
        </Link>
      </div>
    </div>
  );
}
