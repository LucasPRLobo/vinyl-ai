"use client";

import { useEffect, useState } from "react";
import { listGroups, createGroup, joinGroup, type GroupResponse } from "@/lib/api";
import Link from "next/link";

export default function GroupsPage() {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");

  async function loadGroups() {
    try {
      setGroups(await listGroups());
    } catch {
      // Not logged in or error
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadGroups(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setError("");
    try {
      await createGroup(newName);
      setNewName("");
      loadGroups();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create group");
    }
  }

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    if (!inviteCode.trim()) return;
    setError("");
    try {
      await joinGroup(inviteCode);
      setInviteCode("");
      loadGroups();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to join group");
    }
  }

  if (loading) return <p className="text-crate-muted">Loading groups...</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Groups</h1>

      {/* Create / Join */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <form onSubmit={handleCreate} className="space-y-2">
          <p className="text-sm text-crate-muted">Create a group</p>
          <input
            type="text" placeholder="Group name" value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
          />
          <button type="submit" className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 w-full">
            Create
          </button>
        </form>

        <form onSubmit={handleJoin} className="space-y-2">
          <p className="text-sm text-crate-muted">Join with invite code</p>
          <input
            type="text" placeholder="Invite code" value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
            className="w-full px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
          />
          <button type="submit" className="px-4 py-2 bg-crate-blue text-white text-sm font-medium rounded hover:bg-blue-400 w-full">
            Join
          </button>
        </form>
      </div>

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {/* Group list */}
      {groups.length === 0 ? (
        <p className="text-crate-muted">No groups yet. Create one or join with an invite code.</p>
      ) : (
        <div className="space-y-3">
          {groups.map((g) => (
            <div key={g.id} className="border border-crate-border rounded-lg p-4 bg-crate-surface flex justify-between items-center">
              <div>
                <Link href={`/groups/graph?id=${g.id}`} className="font-medium hover:text-crate-accent">
                  {g.name}
                </Link>
                <p className="text-sm text-crate-muted">
                  {g.member_count} member{g.member_count !== 1 ? "s" : ""} &middot; {g.role}
                </p>
                <Link href={`/groups/graph?id=${g.id}`} className="text-xs text-crate-accent hover:underline">
                  View group graph
                </Link>
              </div>
              <div className="text-right">
                <p className="text-xs text-crate-muted">Invite code</p>
                <p className="text-sm font-mono text-crate-accent">{g.invite_code}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
