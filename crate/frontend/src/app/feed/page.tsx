"use client";

import { useEffect, useState } from "react";
import { getMyFeed, type FeedEvent } from "@/lib/api";
import Link from "next/link";

export default function FeedPage() {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyFeed()
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-crate-muted">Loading feed...</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Feed</h1>

      {events.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-crate-muted">No activity yet.</p>
          <p className="text-sm text-crate-muted mt-2">
            Add records or join a group to see activity here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((event) => {
            const albums: string[] = (event.metadata_json?.albums as string[]) || [];

            return (
              <div key={event.id} className="border border-crate-border rounded-lg p-4 bg-crate-surface">
                <div className="flex justify-between items-start">
                  <p className="font-medium text-sm">{event.title}</p>
                  <p className="text-xs text-crate-muted shrink-0 ml-4">
                    {new Date(event.created_at).toLocaleDateString()}
                  </p>
                </div>

                {/* Single record add */}
                {event.event_type === "record_added" && event.body && (
                  <p className="text-sm text-crate-muted mt-1">{event.body}</p>
                )}

                {/* CSV import — show album list */}
                {event.event_type === "csv_import" && albums.length > 0 && (
                  <div className="mt-2">
                    <div className="flex flex-wrap gap-1">
                      {albums.slice(0, 15).map((a, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-crate-bg border border-crate-border">
                          {a}
                        </span>
                      ))}
                      {albums.length > 15 && (
                        <span className="text-xs text-crate-muted px-2 py-0.5">
                          +{albums.length - 15} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Fallback body for other event types */}
                {event.event_type !== "record_added" && event.event_type !== "csv_import" && event.body && (
                  <p className="text-sm text-crate-muted mt-1">{event.body}</p>
                )}

                {event.discogs_id != null && event.discogs_id > 0 && (
                  <Link
                    href={`/record/${event.discogs_id}`}
                    className="text-xs text-crate-accent hover:underline mt-2 inline-block"
                  >
                    View record
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
