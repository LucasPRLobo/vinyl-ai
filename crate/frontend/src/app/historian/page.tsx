"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("crate_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

type Tab = "networks" | "patterns" | "artist-migrations" | "genre-migrations";

export default function HistorianPage() {
  const [tab, setTab] = useState<Tab>("networks");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [narrative, setNarrative] = useState<string | null>(null);

  async function loadTab(t: Tab) {
    setTab(t);
    setData(null);
    setNarrative(null);
    setLoading(true);
    try {
      const endpoints: Record<Tab, string> = {
        "networks": "/historian/invisible-networks",
        "patterns": "/historian/patterns",
        "artist-migrations": "/historian/migrations/artists",
        "genre-migrations": "/historian/migrations/genres",
      };
      const res = await fetch(`${API_BASE}${endpoints[t]}`, { headers: getAuthHeaders() });
      setData(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadMigrationNarrative(migration: any, type: string) {
    setNarrative(null);
    try {
      const res = await fetch(`${API_BASE}/historian/migrations/narrative`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ migration, migration_type: type }),
      });
      const result = await res.json();
      setNarrative(result.narrative);
    } catch (err) {
      console.error(err);
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "networks", label: "Invisible Networks" },
    { key: "patterns", label: "Pattern Discovery" },
    { key: "artist-migrations", label: "Artist Migrations" },
    { key: "genre-migrations", label: "Genre Migrations" },
  ];

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-2">AI Music Historian</h1>
      <p className="text-sm text-crate-muted mb-6">
        Original analysis from your collective data — stories nobody has told before.
      </p>

      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => loadTab(t.key)}
            className={`px-3 py-1.5 text-sm rounded transition-colors ${
              tab === t.key
                ? "bg-crate-accent text-black"
                : "border border-crate-border text-crate-muted hover:text-crate-text"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-crate-accent animate-pulse">Analyzing your graph...</p>}

      {/* Invisible Networks */}
      {tab === "networks" && data && !loading && (
        <div className="space-y-6">
          {data.profiles?.length > 0 && (
            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">Hall of Fame for the Unsung</h2>
              <div className="space-y-3">
                {data.profiles.map((p: any, i: number) => (
                  <div key={i} className="border border-crate-border rounded-lg p-4 bg-crate-surface">
                    <p className="font-medium text-crate-accent">{p.name}</p>
                    <p className="text-xs text-crate-muted uppercase">{p.type}</p>
                    <p className="text-sm mt-2">{p.profile}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.unsung_artists?.length > 0 && (
            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">Most Connected Non-Headliners</h2>
              {data.unsung_artists.slice(0, 10).map((a: any, i: number) => (
                <div key={i} className="flex justify-between text-sm py-1 border-b border-crate-border/50">
                  <span>{a.name} {a.origin_city && <span className="text-crate-muted text-xs">({a.origin_city})</span>}</span>
                  <span className="text-crate-accent">{a.album_count} albums</span>
                </div>
              ))}
            </div>
          )}

          {data.key_studios?.length > 0 && (
            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-crate-muted mb-3">Key Studios</h2>
              {data.key_studios.map((s: any, i: number) => (
                <div key={i} className="flex justify-between text-sm py-1 border-b border-crate-border/50">
                  <span>{s.name} {s.city && <span className="text-crate-muted text-xs">({s.city})</span>}</span>
                  <span className="text-crate-accent">{s.album_count} albums</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Patterns */}
      {tab === "patterns" && data && !loading && (
        <div className="space-y-3">
          {Array.isArray(data) && data.map((p: any, i: number) => (
            <div key={i} className="border border-crate-border rounded-lg p-4 bg-crate-surface">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs px-2 py-0.5 rounded bg-crate-bg border border-crate-border">
                  {p.type.replace(/_/g, " ")}
                </span>
              </div>
              <p className="font-medium text-sm">{p.title}</p>
              {p.explanation && (
                <p className="text-sm text-crate-muted mt-1">{p.explanation}</p>
              )}
            </div>
          ))}
          {Array.isArray(data) && data.length === 0 && (
            <p className="text-crate-muted">No patterns found yet. Add more records to discover patterns.</p>
          )}
        </div>
      )}

      {/* Artist Migrations */}
      {tab === "artist-migrations" && data && !loading && (
        <div className="space-y-4">
          {Array.isArray(data) && data.map((m: any, i: number) => (
            <div key={i} className="border border-crate-border rounded-lg p-4 bg-crate-surface">
              <p className="font-medium">{m.artist}</p>
              {m.origin && <p className="text-xs text-crate-muted">Origin: {m.origin}</p>}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {m.path.map((stop: any, j: number) => (
                  <span key={j} className="flex items-center gap-1">
                    <span className="text-xs px-2 py-1 rounded bg-crate-bg border border-crate-border">
                      {stop.city} {stop.year && <span className="text-crate-muted">({stop.year})</span>}
                    </span>
                    {j < m.path.length - 1 && <span className="text-crate-muted">→</span>}
                  </span>
                ))}
              </div>
              <button
                onClick={() => loadMigrationNarrative(m, "artist")}
                className="text-xs text-crate-accent hover:underline mt-2"
              >
                Tell this story
              </button>
            </div>
          ))}
          {narrative && (
            <div className="border border-crate-accent/30 rounded-lg p-4 bg-crate-surface">
              <p className="text-sm whitespace-pre-wrap">{narrative}</p>
            </div>
          )}
        </div>
      )}

      {/* Genre Migrations */}
      {tab === "genre-migrations" && data && !loading && (
        <div className="space-y-4">
          {Array.isArray(data) && data.map((m: any, i: number) => (
            <div key={i} className="border border-crate-border rounded-lg p-4 bg-crate-surface">
              <p className="font-medium text-crate-accent">{m.genre}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {m.path.map((stop: any, j: number) => (
                  <span key={j} className="flex items-center gap-1">
                    <span className="text-xs px-2 py-1 rounded bg-crate-bg border border-crate-border">
                      {stop.city} {stop.year && <span className="text-crate-muted">({stop.year})</span>}
                      <span className="text-crate-muted ml-1">{stop.album_count} albums</span>
                    </span>
                    {j < m.path.length - 1 && <span className="text-crate-muted">→</span>}
                  </span>
                ))}
              </div>
              <button
                onClick={() => loadMigrationNarrative(m, "genre")}
                className="text-xs text-crate-accent hover:underline mt-2"
              >
                Tell this story
              </button>
            </div>
          ))}
          {narrative && (
            <div className="border border-crate-accent/30 rounded-lg p-4 bg-crate-surface">
              <p className="text-sm whitespace-pre-wrap">{narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
