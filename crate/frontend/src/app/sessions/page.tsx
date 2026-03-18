"use client";

import { useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SessionRecord {
  discogs_id: number;
  title: string;
  reason: string;
  connection_to_next: string | null;
}

interface SessionResult {
  title: string;
  records: SessionRecord[];
  narrative: string;
}

const SUGGESTIONS = [
  "Pick 5 funk records for tonight",
  "A 2-hour journey through jazz",
  "Records featuring flute",
  "All records from the 1970s",
  "Something mellow for a rainy afternoon",
  "A tour of Lagos through music",
  "Records that connect to each other through shared musicians",
  "What should I play for someone who's never listened to Brazilian music?",
];

export default function SessionsPage() {
  const [prompt, setPrompt] = useState("");
  const [session, setSession] = useState<SessionResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate(text?: string) {
    const requestText = text || prompt;
    if (!requestText.trim()) return;
    setLoading(true);
    setSession(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("crate_token") : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API_BASE}/sessions/generate`, {
        method: "POST",
        headers,
        body: JSON.stringify({ prompt: requestText }),
      });
      setSession(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-2">Listening Sessions</h1>
      <p className="text-sm text-crate-muted mb-6">
        Tell me what you're in the mood for. I'll build a session from your collection.
      </p>

      {/* Suggestions */}
      {!session && (
        <div className="grid grid-cols-2 gap-2 mb-6">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => { setPrompt(s); handleGenerate(s); }}
              className="text-left text-xs px-3 py-2 border border-crate-border rounded hover:border-crate-accent transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
          placeholder="What are you in the mood for?"
          className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        <button
          onClick={() => handleGenerate()}
          disabled={loading || !prompt.trim()}
          className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50"
        >
          {loading ? "Building..." : "Generate"}
        </button>
      </div>

      {loading && (
        <p className="text-crate-accent animate-pulse">Building your session...</p>
      )}

      {/* Session result */}
      {session && !loading && (
        <div className="border border-crate-border rounded-lg p-6 bg-crate-surface space-y-4">
          {session.title && (
            <h2 className="text-lg font-bold text-crate-accent">{session.title}</h2>
          )}
          {session.narrative && (
            <p className="text-sm text-crate-muted">{session.narrative}</p>
          )}

          {session.records && session.records.length > 0 && (
            <div className="space-y-3 mt-4">
              {session.records.map((rec, i) => (
                <div key={i} className="border border-crate-border rounded p-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-crate-muted w-6">{i + 1}.</span>
                    <Link
                      href={`/record/${rec.discogs_id}`}
                      className="font-medium text-sm hover:text-crate-accent"
                    >
                      {rec.title}
                    </Link>
                  </div>
                  <p className="text-xs text-crate-muted ml-8 mt-1">{rec.reason}</p>
                  {rec.connection_to_next && (
                    <p className="text-xs text-crate-accent ml-8 mt-1">
                      → {rec.connection_to_next}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          <button
            onClick={() => { setSession(null); setPrompt(""); }}
            className="text-sm text-crate-muted hover:text-crate-text mt-4"
          >
            Build another session
          </button>
        </div>
      )}
    </div>
  );
}
