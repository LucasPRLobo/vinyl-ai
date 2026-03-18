"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import { getFullGraph, explorNode } from "@/lib/api";
import type { GraphNode, GraphEdge } from "@/lib/types";

// react-force-graph must be loaded client-side only
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const LABEL_COLORS: Record<string, string> = {
  Album: "#f59e0b",
  Artist: "#3b82f6",
  Label: "#22c55e",
  Genre: "#a855f7",
  Studio: "#ec4899",
  Scene: "#f97316",
  City: "#06b6d4",
  Instrument: "#84cc16",
  Pressing: "#737373",
};

interface ForceNode {
  id: string;
  name: string;
  label: string;
  color: string;
  val: number;
}

interface ForceLink {
  source: string;
  target: string;
  type: string;
}

export default function GraphPage() {
  const [nodes, setNodes] = useState<ForceNode[]>([]);
  const [links, setLinks] = useState<ForceLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ForceNode | null>(null);
  const [selectedConnections, setSelectedConnections] = useState<
    { relationship: string; target_name: string; target_labels: string[] }[]
  >([]);
  const graphRef = useRef<any>(null);

  useEffect(() => {
    getFullGraph()
      .then((data) => {
        const forceNodes: ForceNode[] = data.nodes.map((n: GraphNode) => ({
          id: n.id,
          name: n.name || "?",
          label: n.label,
          color: LABEL_COLORS[n.label] || "#737373",
          val: n.label === "Album" ? 3 : 1,
        }));
        const forceLinks: ForceLink[] = data.edges.map((e: GraphEdge) => ({
          source: e.source,
          target: e.target,
          type: e.type,
        }));
        setNodes(forceNodes);
        setLinks(forceLinks);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleNodeClick = useCallback(async (node: ForceNode) => {
    setSelected(node);
    try {
      const result = await explorNode(node.label, node.name);
      setSelectedConnections(
        result.connections.map((c) => ({
          relationship: c.relationship,
          target_name: c.target_name,
          target_labels: c.target_labels,
        }))
      );
    } catch {
      setSelectedConnections([]);
    }
  }, []);

  if (loading) {
    return <p className="text-crate-muted">Loading graph...</p>;
  }

  if (nodes.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-crate-muted text-lg">No graph data yet.</p>
        <p className="text-sm text-crate-muted mt-2">Add some records to see your knowledge graph.</p>
      </div>
    );
  }

  return (
    <div className="flex gap-6">
      {/* Graph */}
      <div className="flex-1 border border-crate-border rounded-lg overflow-hidden bg-crate-surface" style={{ height: "70vh" }}>
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes, links }}
          nodeLabel={(node: any) => `${node.label}: ${node.name}`}
          nodeColor={(node: any) => node.color}
          nodeRelSize={5}
          linkColor={() => "#333"}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkLabel={(link: any) => link.type}
          onNodeClick={(node: any) => handleNodeClick(node)}
          backgroundColor="#141414"
          nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const fontSize = 10 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.fillStyle = node.color;
            ctx.beginPath();
            const r = node.label === "Album" ? 5 : 3;
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
            ctx.fill();
            if (globalScale > 1.5) {
              ctx.fillStyle = "#e5e5e5";
              ctx.textAlign = "center";
              ctx.fillText(node.name, node.x, node.y + r + fontSize + 1);
            }
          }}
        />
      </div>

      {/* Sidebar */}
      <div className="w-72 shrink-0">
        {/* Legend */}
        <div className="mb-6">
          <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Legend</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(LABEL_COLORS).map(([label, color]) => (
              <span key={label} className="flex items-center gap-1 text-xs">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* Selected node */}
        {selected && (
          <div className="border border-crate-border rounded-lg p-4 bg-crate-surface">
            <p className="text-xs text-crate-muted uppercase tracking-wide">{selected.label}</p>
            <p className="font-medium mt-1">{selected.name}</p>

            {selectedConnections.length > 0 && (
              <div className="mt-3 space-y-1">
                <p className="text-xs text-crate-muted">{selectedConnections.length} connections:</p>
                {selectedConnections.slice(0, 20).map((c, i) => (
                  <p key={i} className="text-xs">
                    <span className="text-crate-muted">{c.relationship}</span>{" "}
                    <span style={{ color: LABEL_COLORS[c.target_labels[0]] || "#e5e5e5" }}>
                      {c.target_name}
                    </span>
                  </p>
                ))}
                {selectedConnections.length > 20 && (
                  <p className="text-xs text-crate-muted">
                    +{selectedConnections.length - 20} more
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div className="mt-4 text-xs text-crate-muted">
          <p>{nodes.length} nodes &middot; {links.length} edges</p>
          <p className="mt-1">Click a node to explore. Scroll to zoom. Drag to pan.</p>
        </div>
      </div>
    </div>
  );
}
