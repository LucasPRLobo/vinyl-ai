"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("crate_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authFetch(url: string) {
  const res = await fetch(url, { headers: getAuthHeaders() });
  return res.json();
}

type Tab = "dna" | "temporal" | "uncharted" | "thread";

export default function InsightsPage() {
  const [tab, setTab] = useState<Tab>("dna");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Thread inputs
  const [threadId1, setThreadId1] = useState("");
  const [threadId2, setThreadId2] = useState("");

  async function loadInsight(type: Tab) {
    setTab(type);
    setData(null);
    setLoading(true);
    try {
      let url = "";
      if (type === "dna") url = `${API_BASE}/insights/dna`;
      else if (type === "temporal") url = `${API_BASE}/insights/temporal`;
      else if (type === "uncharted") url = `${API_BASE}/insights/uncharted`;
      if (url) {
        setData(await authFetch(url));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadThread() {
    if (!threadId1 || !threadId2) return;
    setLoading(true);
    setData(null);
    try {
      const res = await fetch(
        `${API_BASE}/insights/thread?album_id_1=${threadId1}&album_id_2=${threadId2}`
      );
      setData(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "dna", label: "Collection DNA" },
    { key: "temporal", label: "Temporal" },
    { key: "uncharted", label: "Uncharted Territory" },
    { key: "thread", label: "The Thread" },
  ];

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Insights</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => t.key !== "thread" ? loadInsight(t.key) : setTab("thread")}
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

      {/* Thread inputs */}
      {tab === "thread" && (
        <div className="flex gap-3 mb-6">
          <input
            type="number" placeholder="Album Discogs ID 1" value={threadId1}
            onChange={(e) => setThreadId1(e.target.value)}
            className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
          />
          <input
            type="number" placeholder="Album Discogs ID 2" value={threadId2}
            onChange={(e) => setThreadId2(e.target.value)}
            className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
          />
          <button
            onClick={loadThread}
            disabled={loading || !threadId1 || !threadId2}
            className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50"
          >
            Connect
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && <p className="text-crate-accent animate-pulse">Generating insight...</p>}

      {/* Results */}
      {data && !loading && (
        <div className="border border-crate-border rounded-lg p-6 bg-crate-surface space-y-4">
          {/* Narrative (DNA, Thread, Temporal all have this) */}
          {data.narrative && (
            <div className="prose prose-invert max-w-none">
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{data.narrative}</p>
            </div>
          )}

          {/* Decades (Temporal + DNA) */}
          {data.decades && (
            <div className="mt-4">
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Decade breakdown</p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(data.decades as Record<string, { count: number }>).map(([decade, info]) => (
                  <span key={decade} className="text-xs px-2 py-1 rounded bg-crate-bg border border-crate-border">
                    {decade}s: {info.count}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Uncharted Territory */}
          {Array.isArray(data) && data.length > 0 && (
            <div className="space-y-3">
              {data.map((item: any, i: number) => (
                <div key={i} className="border border-crate-border rounded p-3">
                  <p className="font-medium text-sm text-crate-accent">{item.scene}</p>
                  {item.city && <p className="text-xs text-crate-muted">{item.city}</p>}
                  {item.era_start && (
                    <p className="text-xs text-crate-muted">{item.era_start}–{item.era_end || "?"}</p>
                  )}
                  <p className="text-xs text-crate-muted mt-1">
                    {item.available} available albums via {item.via_artists?.join(", ")}
                  </p>
                  {item.sample_albums && (
                    <p className="text-xs text-crate-muted mt-1">
                      e.g. {item.sample_albums.slice(0, 3).join(", ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Thread path */}
          {data.path && data.path.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Connection path</p>
              <div className="flex items-center gap-2 flex-wrap">
                {data.path.map((node: any, i: number) => (
                  <span key={i} className="flex items-center gap-1">
                    <span className="text-xs px-2 py-1 rounded bg-crate-bg border border-crate-border">
                      {node.name}
                    </span>
                    {i < data.path.length - 1 && (
                      <span className="text-crate-muted text-xs">→</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
