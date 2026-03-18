"use client";

import { useState, useRef } from "react";
import { searchRelease, addRecord, importCsv } from "@/lib/api";
import type { SearchResult, AddResponse } from "@/lib/types";

export default function AddRecordPage() {
  const [artist, setArtist] = useState("");
  const [title, setTitle] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addResult, setAddResult] = useState<AddResponse | null>(null);
  const [error, setError] = useState("");

  // CSV import state
  const [csvMode, setCsvMode] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvResult, setCsvResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!artist.trim() || !title.trim()) return;
    setSearching(true);
    setError("");
    setResults([]);
    setAddResult(null);
    try {
      const res = await searchRelease(artist, title);
      setResults(res);
      if (res.length === 0) setError("No results found. Check the artist/title.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleAdd(result: SearchResult) {
    setAdding(true);
    setError("");
    try {
      const res = await addRecord(result.discogs_id, result.musicbrainz_id);
      setAddResult(res);
      setResults([]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add record");
    } finally {
      setAdding(false);
    }
  }

  async function handleCsvImport(quick: boolean) {
    if (!csvFile) return;
    setCsvImporting(true);
    setCsvResult(null);
    setError("");

    try {
      const result = await importCsv(csvFile, quick);
      setCsvResult(result);
      setCsvFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "CSV import failed");
    } finally {
      setCsvImporting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Add Record</h1>

      {/* Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setCsvMode(false)}
          className={`px-3 py-1.5 text-sm rounded transition-colors ${
            !csvMode ? "bg-crate-accent text-black" : "border border-crate-border text-crate-muted hover:text-crate-text"
          }`}
        >
          Search
        </button>
        <button
          onClick={() => setCsvMode(true)}
          className={`px-3 py-1.5 text-sm rounded transition-colors ${
            csvMode ? "bg-crate-accent text-black" : "border border-crate-border text-crate-muted hover:text-crate-text"
          }`}
        >
          Import Discogs CSV
        </button>
      </div>

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {/* === CSV IMPORT MODE === */}
      {csvMode && (
        <div className="space-y-4">
          <p className="text-sm text-crate-muted">
            Export your collection from Discogs: Settings &gt; Collection &gt; Export.
            Then upload the CSV here.
          </p>

          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-crate-muted file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-crate-accent file:text-black hover:file:bg-amber-400"
          />

          {csvFile && (
            <div className="space-y-2">
              <p className="text-sm">
                Selected: <span className="text-crate-accent">{csvFile.name}</span> ({(csvFile.size / 1024).toFixed(1)} KB)
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => handleCsvImport(true)}
                  disabled={csvImporting}
                  className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50"
                >
                  {csvImporting ? "Importing..." : "Quick Import (basic data, fast)"}
                </button>
                <button
                  onClick={() => handleCsvImport(false)}
                  disabled={csvImporting}
                  className="px-4 py-2 border border-crate-border text-sm rounded hover:border-crate-accent disabled:opacity-50"
                >
                  {csvImporting ? "Importing..." : "Full Import (AI research, slow)"}
                </button>
              </div>

              <p className="text-xs text-crate-muted">
                Quick: imports basic data instantly, enrich later. Full: runs AI research per record (slow for large collections).
              </p>
            </div>
          )}

          {csvImporting && (
            <div className="border border-crate-border rounded-lg p-6 bg-crate-surface">
              <p className="text-crate-accent animate-pulse">Importing collection...</p>
              <p className="text-xs text-crate-muted mt-2">This may take a while for large collections.</p>
            </div>
          )}

          {csvResult && (
            <div className="border border-crate-green/30 rounded-lg p-6 bg-crate-surface space-y-2">
              <p className="text-crate-green font-medium">Import complete!</p>
              <p className="text-sm text-crate-muted">Total in CSV: {csvResult.total_in_csv}</p>
              <p className="text-sm text-crate-muted">Imported: {csvResult.imported}</p>
              {csvResult.errors > 0 && (
                <p className="text-sm text-red-400">Errors: {csvResult.errors}</p>
              )}
              <p className="text-sm text-crate-muted">Mode: {csvResult.mode}</p>
            </div>
          )}
        </div>
      )}

      {/* === SEARCH MODE === */}
      {!csvMode && (
        <>
          <form onSubmit={handleSearch} className="flex gap-3 mb-6">
            <input
              type="text"
              placeholder="Artist"
              value={artist}
              onChange={(e) => setArtist(e.target.value)}
              className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
            />
            <input
              type="text"
              placeholder="Album title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
            />
            <button
              type="submit"
              disabled={searching}
              className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50 transition-colors"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </form>

          {/* Search Results */}
          {results.length > 0 && (
            <div className="space-y-2 mb-6">
              <p className="text-sm text-crate-muted">Select a release:</p>
              {results.map((r) => (
                <button
                  key={r.discogs_id}
                  onClick={() => handleAdd(r)}
                  disabled={adding}
                  className="w-full text-left border border-crate-border rounded-lg p-4 hover:border-crate-accent transition-colors bg-crate-surface disabled:opacity-50"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{r.title}</p>
                      <p className="text-sm text-crate-muted">
                        {r.year || "?"} &middot; {r.country || "?"}{" "}
                        {r.musicbrainz_id && (
                          <span className="text-crate-blue text-xs">[+MusicBrainz]</span>
                        )}
                      </p>
                    </div>
                    {r.cover_url && (
                      <img
                        src={r.cover_url}
                        alt=""
                        className="w-12 h-12 rounded object-cover ml-3"
                      />
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Adding state */}
          {adding && (
            <div className="border border-crate-border rounded-lg p-6 bg-crate-surface">
              <p className="text-crate-accent animate-pulse">
                Researching... Fetching credits, history, and connections.
              </p>
              <p className="text-xs text-crate-muted mt-2">This may take 10-30 seconds.</p>
            </div>
          )}

          {/* Add Result */}
          {addResult && (
            <div className="border border-crate-green/30 rounded-lg p-6 bg-crate-surface space-y-4">
              <div>
                <p className="text-crate-green font-medium">Added: {addResult.album_title}</p>
                <p className="text-sm text-crate-muted">
                  {addResult.artists_added} artists/credits ingested into graph
                </p>
              </div>

              {addResult.connections_found.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">New connections:</p>
                  {addResult.connections_found.map((c, i) => (
                    <p key={i} className="text-sm text-crate-muted">
                      {c.connection_type === "shared_artist"
                        ? `${c.shared_artist} also on: ${c.also_on.join(", ")}`
                        : `Label "${c.shared_label}" also on: ${c.also_on.join(", ")}`}
                    </p>
                  ))}
                </div>
              )}

              {addResult.insights && addResult.insights.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Did you know?</p>
                  {addResult.insights.map((insight, i) => (
                    <p key={i} className="text-sm text-crate-accent">{insight.text}</p>
                  ))}
                </div>
              )}

              <button
                onClick={() => {
                  setAddResult(null);
                  setArtist("");
                  setTitle("");
                }}
                className="text-sm text-crate-muted hover:text-crate-text"
              >
                Add another record
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
