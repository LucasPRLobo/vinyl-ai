"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("crate_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

interface MapPoint {
  city: string;
  lat: number;
  lng: number;
  count: number;
  albums: { title: string; discogs_id: number }[];
}

interface CityDetail {
  city: string;
  scenes: { scene: string; era_start: number | null; era_end: number | null; albums: string[]; album_count: number }[];
  artists: { artist: string; albums: string[] }[];
}

export default function MapPage() {
  const [points, setPoints] = useState<MapPoint[]>([]);
  const [selectedCity, setSelectedCity] = useState<CityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [storePoints, setStorePoints] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/map/sound`, { headers: getAuthHeaders() }).then((r) => r.json()),
      fetch(`${API_BASE}/stores/map`, { headers: getAuthHeaders() }).then((r) => r.json()).catch(() => []),
    ])
      .then(([soundData, storeData]) => {
        setPoints(soundData);
        setStorePoints(storeData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleCityClick(cityName: string) {
    try {
      const res = await fetch(`${API_BASE}/map/city/${encodeURIComponent(cityName)}`);
      setSelectedCity(await res.json());
    } catch {
      setSelectedCity(null);
    }
  }

  if (loading) return <p className="text-crate-muted">Loading map data...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Sound Map</h1>
      <p className="text-sm text-crate-muted mb-6">
        Your collection plotted by where the music came from. {points.length} cities.
      </p>

      <div className="flex gap-6">
        {/* Map placeholder — Mapbox integration requires the token and npm package at runtime */}
        <div className="flex-1 border border-crate-border rounded-lg bg-crate-surface p-6" style={{ minHeight: "60vh" }}>
          <p className="text-xs text-crate-muted mb-4">
            Map visualization requires Mapbox GL JS. Below is the data view.
          </p>

          {/* City list sorted by count */}
          <div className="space-y-2">
            {points.map((p) => (
              <button
                key={p.city}
                onClick={() => handleCityClick(p.city)}
                className="w-full text-left flex items-center justify-between px-3 py-2 rounded border border-crate-border hover:border-crate-accent transition-colors"
              >
                <div>
                  <span className="font-medium text-sm">{p.city}</span>
                  <span className="text-xs text-crate-muted ml-2">
                    ({p.lat.toFixed(1)}, {p.lng.toFixed(1)})
                  </span>
                </div>
                <span className="text-crate-accent font-medium text-sm">{p.count} records</span>
              </button>
            ))}
          </div>

          {storePoints.length > 0 && (
            <div className="mt-6">
              <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Record Stores</p>
              {storePoints.map((s: any) => (
                <div key={s.id} className="text-sm text-crate-muted py-1">
                  {s.name} — {s.city} {s.specialties && <span className="text-xs">({s.specialties})</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* City detail sidebar */}
        <div className="w-80 shrink-0">
          {selectedCity ? (
            <div className="border border-crate-border rounded-lg p-4 bg-crate-surface">
              <h2 className="font-bold text-lg mb-3">{selectedCity.city}</h2>

              {selectedCity.scenes.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Scenes</p>
                  {selectedCity.scenes.map((s, i) => (
                    <div key={i} className="mb-2">
                      <p className="text-sm font-medium text-crate-accent">{s.scene}</p>
                      {s.era_start && (
                        <p className="text-xs text-crate-muted">{s.era_start}–{s.era_end || "?"}</p>
                      )}
                      <p className="text-xs text-crate-muted">{s.album_count} albums</p>
                    </div>
                  ))}
                </div>
              )}

              {selectedCity.artists.length > 0 && (
                <div>
                  <p className="text-xs text-crate-muted uppercase tracking-wide mb-2">Artists from here</p>
                  {selectedCity.artists.map((a, i) => (
                    <div key={i} className="text-sm mb-1">
                      <span className="font-medium">{a.artist}</span>
                      <span className="text-xs text-crate-muted ml-1">
                        ({a.albums.slice(0, 2).join(", ")})
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-crate-muted">Click a city to explore its music history.</p>
          )}
        </div>
      </div>
    </div>
  );
}
