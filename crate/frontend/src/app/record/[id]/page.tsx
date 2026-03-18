"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getRecord } from "@/lib/api";
import Link from "next/link";

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
  Track: "#737373",
};

interface RecordConnection {
  rel_type: string;
  labels: string[];
  props: Record<string, unknown>;
  rel_props: Record<string, unknown>;
}

interface RecordContext {
  historical_note: string;
  significance: string;
  anecdotes: string | null;
  confidence: string | null;
  sources_used: string | null;
}

export default function RecordPage() {
  const params = useParams();
  const id = Number(params.id);
  const [connections, setConnections] = useState<RecordConnection[]>([]);
  const [context, setContext] = useState<RecordContext | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecord(id)
      .then((data: any) => {
        setConnections(data.connections);
        setContext(data.context);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-crate-muted">Loading record... (context may be generating)</p>;

  // Group connections by type
  const grouped: Record<string, RecordConnection[]> = {};
  for (const c of connections) {
    const label = c.labels[0] || "Other";
    if (!grouped[label]) grouped[label] = [];
    grouped[label].push(c);
  }

  const albumTitle =
    connections.find((c) => c.labels.includes("Album"))?.props?.title ||
    `Record ${id}`;

  return (
    <div className="max-w-3xl">
      <Link href="/" className="text-sm text-crate-muted hover:text-crate-text">
        &larr; Back to collection
      </Link>

      <h1 className="text-2xl font-bold mt-4 mb-1">{String(albumTitle)}</h1>
      <p className="text-sm text-crate-muted mb-6">Discogs ID: {id}</p>

      {/* Context — generated on first view, cached forever */}
      {context && (
        <div className="border border-crate-border rounded-lg p-5 bg-crate-surface mb-6 space-y-3">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-crate-muted uppercase tracking-wide">AI-Generated Context</p>
            <div className="flex items-center gap-2">
              {context.confidence && (
                <span className={`text-xs px-2 py-0.5 rounded ${
                  context.confidence === "high"
                    ? "bg-crate-green/20 text-crate-green"
                    : "bg-crate-accent/20 text-crate-accent"
                }`}>
                  {context.confidence} confidence
                </span>
              )}
              {context.sources_used && (
                <span className="text-xs text-crate-muted">{context.sources_used}</span>
              )}
            </div>
          </div>
          {context.historical_note && (
            <div>
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-1">Historical Context</p>
              <p className="text-sm leading-relaxed">{context.historical_note}</p>
            </div>
          )}
          {context.significance && (
            <div>
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-1">Significance</p>
              <p className="text-sm leading-relaxed">{context.significance}</p>
            </div>
          )}
          {context.anecdotes && (
            <div>
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-1">Behind the Scenes</p>
              <p className="text-sm leading-relaxed">{context.anecdotes}</p>
            </div>
          )}
        </div>
      )}

      {/* Connections */}
      <div className="space-y-6">
        {Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([label, items]) => (
            <div key={label}>
              <h2 className="text-sm font-medium mb-2 flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: LABEL_COLORS[label] || "#737373" }}
                />
                {label}s ({items.length})
              </h2>
              <div className="space-y-1">
                {items.map((item, i) => {
                  const name = String(
                    item.props.name || item.props.title || item.props.position || "?"
                  );
                  const relType = item.rel_type.replace(/_/g, " ").toLowerCase();
                  const instrument = item.rel_props?.instrument;
                  const tracks = item.rel_props?.tracks;

                  return (
                    <div
                      key={i}
                      className="flex items-center justify-between text-sm px-3 py-2 rounded bg-crate-surface border border-crate-border"
                    >
                      <div>
                        <span className="font-medium">{name}</span>
                        {instrument && (
                          <span className="text-crate-muted ml-2">({String(instrument)})</span>
                        )}
                        {tracks && (
                          <span className="text-crate-muted ml-2">tracks: {String(tracks)}</span>
                        )}
                      </div>
                      <span className="text-xs text-crate-muted">{relType}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
