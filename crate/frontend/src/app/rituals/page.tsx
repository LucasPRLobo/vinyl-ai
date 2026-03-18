"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("crate_token");
}

export default function RitualsPage() {
  const [groupId, setGroupId] = useState("");
  const [rotations, setRotations] = useState<any[]>([]);
  const [challenges, setChallenges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // New rotation form
  const [rotDiscogs, setRotDiscogs] = useState("");
  const [rotTitle, setRotTitle] = useState("");
  const [newBriefing, setNewBriefing] = useState<string | null>(null);

  async function loadRituals() {
    if (!groupId) return;
    setLoading(true);
    try {
      const [rot, chal] = await Promise.all([
        fetch(`${API_BASE}/historian/rotation/${groupId}`).then(r => r.json()),
        fetch(`${API_BASE}/historian/dig-challenge/${groupId}`).then(r => r.json()),
      ]);
      setRotations(rot);
      setChallenges(chal);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function createRotation() {
    if (!rotDiscogs || !rotTitle || !groupId) return;
    setLoading(true);
    setNewBriefing(null);
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/historian/rotation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ group_id: groupId, discogs_id: parseInt(rotDiscogs), album_title: rotTitle }),
      });
      const result = await res.json();
      setNewBriefing(result.briefing);
      setRotDiscogs("");
      setRotTitle("");
      loadRituals();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function generateChallenge() {
    if (!groupId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/historian/dig-challenge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_id: groupId }),
      });
      await res.json();
      loadRituals();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-2">Group Rituals</h1>
      <p className="text-sm text-crate-muted mb-6">
        Monthly rotation, dig challenges, and more.
      </p>

      {/* Group selector */}
      <div className="flex gap-3 mb-6">
        <input
          type="text" placeholder="Group ID" value={groupId}
          onChange={e => setGroupId(e.target.value)}
          className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        <button onClick={loadRituals} disabled={!groupId || loading}
          className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50">
          Load
        </button>
      </div>

      {loading && <p className="text-crate-accent animate-pulse">Loading...</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rotation */}
        <div>
          <h2 className="font-medium mb-3">The Rotation</h2>
          <p className="text-xs text-crate-muted mb-3">Pick a record for the group to listen to this month.</p>

          <div className="space-y-2 mb-4">
            <input type="number" placeholder="Discogs ID" value={rotDiscogs}
              onChange={e => setRotDiscogs(e.target.value)}
              className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent" />
            <input type="text" placeholder="Album title" value={rotTitle}
              onChange={e => setRotTitle(e.target.value)}
              className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent" />
            <button onClick={createRotation} disabled={!rotDiscogs || !rotTitle || loading}
              className="w-full px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50">
              Pick for this month
            </button>
          </div>

          {newBriefing && (
            <div className="border border-crate-accent/30 rounded-lg p-3 bg-crate-surface mb-4">
              <p className="text-xs text-crate-muted mb-1">AI Briefing</p>
              <p className="text-sm whitespace-pre-wrap">{newBriefing}</p>
            </div>
          )}

          {rotations.map((r, i) => (
            <div key={i} className="border border-crate-border rounded p-3 bg-crate-surface mb-2">
              <p className="text-xs text-crate-muted">{r.month} — picked by {r.picker}</p>
              <Link href={`/record/${r.discogs_id}`} className="font-medium text-sm hover:text-crate-accent">
                {r.album}
              </Link>
            </div>
          ))}
        </div>

        {/* Dig Challenge */}
        <div>
          <h2 className="font-medium mb-3">Dig Challenge</h2>
          <p className="text-xs text-crate-muted mb-3">Find something from a white space in the group's graph.</p>

          <button onClick={generateChallenge} disabled={!groupId || loading}
            className="w-full px-4 py-2 bg-crate-blue text-white text-sm font-medium rounded hover:bg-blue-400 disabled:opacity-50 mb-4">
            Generate new challenge
          </button>

          {challenges.map((c, i) => (
            <div key={i} className="border border-crate-border rounded p-3 bg-crate-surface mb-2">
              <p className="text-xs text-crate-muted">{c.month}</p>
              <p className="text-sm">{c.challenge}</p>
              <p className="text-xs text-crate-accent mt-1">Target: {c.target}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
