"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { getGroupGraph, explorNode } from "@/lib/api";
import Link from "next/link";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const LABEL_COLORS: Record<string, string> = {
  Artist: "#3b82f6",
  Label: "#22c55e",
  Genre: "#a855f7",
  Studio: "#ec4899",
  Scene: "#f97316",
  City: "#06b6d4",
  Instrument: "#84cc16",
};

interface Member {
  id: string;
  name: string;
  color: string;
}

interface GroupNode {
  id: string;
  label: string;
  name: string;
  owners: string[];
  owner_ids: string[];
  shared: boolean;
  props: Record<string, unknown>;
  // Force graph internal
  x?: number;
  y?: number;
  color?: string;
  val?: number;
}

interface GroupEdge {
  source: string;
  target: string;
  type: string;
}

export default function GroupGraphPage() {
  const searchParams = useSearchParams();
  const groupId = searchParams.get("id");

  const [nodes, setNodes] = useState<GroupNode[]>([]);
  const [edges, setEdges] = useState<GroupEdge[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<GroupNode | null>(null);
  const [selectedConnections, setSelectedConnections] = useState<any[]>([]);
  const [filter, setFilter] = useState<string | null>(null); // null = all, member id = filter
  const graphRef = useRef<any>(null);

  useEffect(() => {
    if (!groupId) return;
    getGroupGraph(groupId)
      .then((data) => {
        setNodes(data.nodes);
        setEdges(data.edges);
        setMembers(data.members);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [groupId]);

  const handleNodeClick = useCallback(async (node: any) => {
    setSelected(node);
    if (node.label && node.name) {
      try {
        const result = await explorNode(node.label, node.name);
        setSelectedConnections(result.connections || []);
      } catch {
        setSelectedConnections([]);
      }
    }
  }, []);

  // Build member color map
  const memberColorMap: Record<string, string> = {};
  members.forEach((m) => { memberColorMap[m.id] = m.color; });

  // Filter nodes if a member is selected
  const visibleNodeIds = new Set<string>();
  const filteredNodes = filter
    ? nodes.filter((n) => {
        if (n.label !== "Album") return true; // Non-album nodes always visible
        const visible = n.owner_ids.includes(filter);
        if (visible) visibleNodeIds.add(n.id);
        return visible;
      })
    : nodes;

  // For filtered view, also show non-album nodes connected to visible albums
  const filteredEdges = filter
    ? edges.filter((e) => {
        const srcVisible = visibleNodeIds.has(typeof e.source === "string" ? e.source : (e.source as any).id);
        const tgtVisible = visibleNodeIds.has(typeof e.target === "string" ? e.target : (e.target as any).id);
        return srcVisible || tgtVisible;
      })
    : edges;

  if (!groupId) {
    return (
      <div className="text-center py-20">
        <p className="text-crate-muted">No group selected.</p>
        <Link href="/groups" className="text-crate-accent hover:underline text-sm">Go to Groups</Link>
      </div>
    );
  }

  if (loading) return <p className="text-crate-muted">Loading group graph...</p>;

  if (nodes.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-crate-muted text-lg">No records in this group yet.</p>
        <p className="text-sm text-crate-muted mt-2">Members need to add records to their collections.</p>
      </div>
    );
  }

  const sharedCount = nodes.filter((n) => n.shared).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Group Graph</h1>
          <p className="text-sm text-crate-muted">
            {nodes.length} nodes &middot; {edges.length} edges &middot; {sharedCount} shared albums
          </p>
        </div>
        <Link href="/groups" className="text-sm text-crate-muted hover:text-crate-text">
          &larr; Back to Groups
        </Link>
      </div>

      <div className="flex gap-6">
        {/* Graph */}
        <div
          className="flex-1 border border-crate-border rounded-lg overflow-hidden bg-crate-surface"
          style={{ height: "70vh" }}
        >
          <ForceGraph2D
            ref={graphRef}
            graphData={{ nodes: filteredNodes, links: filteredEdges }}
            nodeLabel={(node: any) =>
              node.label === "Album" && node.owners?.length
                ? `${node.name} (${node.owners.join(", ")})`
                : `${node.label}: ${node.name}`
            }
            nodeRelSize={5}
            linkColor={() => "#333"}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            backgroundColor="#141414"
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const x = node.x || 0;
              const y = node.y || 0;

              if (node.label === "Album") {
                const ownerIds: string[] = node.owner_ids || [];
                const isShared = ownerIds.length > 1;
                const baseR = isShared ? 6 : 4;

                if (ownerIds.length === 1) {
                  // Single owner — solid color
                  ctx.fillStyle = memberColorMap[ownerIds[0]] || "#f59e0b";
                  ctx.beginPath();
                  ctx.arc(x, y, baseR, 0, 2 * Math.PI);
                  ctx.fill();
                } else if (ownerIds.length > 1) {
                  // Multiple owners — pie chart style
                  const sliceAngle = (2 * Math.PI) / ownerIds.length;
                  ownerIds.forEach((oid, i) => {
                    ctx.fillStyle = memberColorMap[oid] || "#737373";
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.arc(x, y, baseR, i * sliceAngle, (i + 1) * sliceAngle);
                    ctx.closePath();
                    ctx.fill();
                  });
                  // White center dot to indicate shared
                  ctx.fillStyle = "#ffffff";
                  ctx.beginPath();
                  ctx.arc(x, y, 1.5, 0, 2 * Math.PI);
                  ctx.fill();
                }
              } else {
                // Non-album nodes — standard color by type
                const r = 3;
                ctx.fillStyle = LABEL_COLORS[node.label] || "#737373";
                ctx.beginPath();
                ctx.arc(x, y, r, 0, 2 * Math.PI);
                ctx.fill();
              }

              // Labels at zoom
              if (globalScale > 1.5) {
                const fontSize = 10 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.fillStyle = "#e5e5e5";
                ctx.textAlign = "center";
                ctx.fillText(node.name, x, y + (node.label === "Album" ? 8 : 5));
              }
            }}
          />
        </div>

        {/* Sidebar */}
        <div className="w-72 shrink-0 space-y-4">
          {/* Member filter */}
          <div>
            <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Members</p>
            <button
              onClick={() => setFilter(null)}
              className={`block w-full text-left text-sm px-2 py-1 rounded mb-1 ${
                filter === null ? "bg-crate-border text-crate-text" : "text-crate-muted hover:text-crate-text"
              }`}
            >
              All members
            </button>
            {members.map((m) => (
              <button
                key={m.id}
                onClick={() => setFilter(filter === m.id ? null : m.id)}
                className={`flex items-center gap-2 w-full text-left text-sm px-2 py-1 rounded mb-1 ${
                  filter === m.id ? "bg-crate-border text-crate-text" : "text-crate-muted hover:text-crate-text"
                }`}
              >
                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: m.color }} />
                {m.name}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div>
            <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Node types</p>
            <div className="space-y-1">
              {Object.entries(LABEL_COLORS).map(([label, color]) => (
                <span key={label} className="flex items-center gap-1.5 text-xs">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                  {label}
                </span>
              ))}
              <span className="flex items-center gap-1.5 text-xs">
                <span className="w-3 h-3 rounded-full border-2 border-white bg-crate-bg" />
                Shared album (multi-color)
              </span>
            </div>
          </div>

          {/* Selected node detail */}
          {selected && (
            <div className="border border-crate-border rounded-lg p-3 bg-crate-surface">
              <p className="text-xs text-crate-muted uppercase">{selected.label}</p>
              <p className="font-medium mt-0.5">{selected.name}</p>

              {selected.owners && selected.owners.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-crate-muted">
                    Owned by: {selected.owners.join(", ")}
                  </p>
                </div>
              )}

              {selectedConnections.length > 0 && (
                <div className="mt-2 space-y-0.5">
                  <p className="text-xs text-crate-muted">{selectedConnections.length} connections:</p>
                  {selectedConnections.slice(0, 15).map((c: any, i: number) => (
                    <p key={i} className="text-xs">
                      <span className="text-crate-muted">{c.relationship}</span>{" "}
                      {c.target_name}
                    </p>
                  ))}
                </div>
              )}

              {selected.props?.discogs_id && (
                <Link
                  href={`/record/${selected.props.discogs_id}`}
                  className="text-xs text-crate-accent hover:underline mt-2 block"
                >
                  View record
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
