"use client";

import { useState } from "react";
import { queryGraph } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  cypher?: string;
}

export default function QueryPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await queryGraph(question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, cypher: res.cypher },
      ]);
    } catch (err: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Something went wrong.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-2">Ask Your Collection</h1>
      <p className="text-sm text-crate-muted mb-6">
        Ask anything about your records, connections, history, or scenes.
      </p>

      {/* Suggestions */}
      {messages.length === 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-8">
          {[
            "Who appears on the most albums in my collection?",
            "What connects my Brazilian records to my jazz records?",
            "Which labels are most common in my collection?",
            "Show me records from the 1970s",
            "What genres do I have?",
            "Find session musicians who appear on multiple albums",
          ].map((q) => (
            <button
              key={q}
              onClick={() => {
                setInput(q);
              }}
              className="text-left text-xs px-3 py-2 border border-crate-border rounded hover:border-crate-accent transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="space-y-4 mb-6">
        {messages.map((msg, i) => (
          <div key={i}>
            <p className="text-xs text-crate-muted mb-1">
              {msg.role === "user" ? "You" : "Crate"}
            </p>
            <div
              className={`rounded-lg p-4 text-sm ${
                msg.role === "user"
                  ? "bg-crate-surface border border-crate-border"
                  : "bg-crate-surface border border-crate-accent/20"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.cypher && (
                <details className="mt-3">
                  <summary className="text-xs text-crate-muted cursor-pointer hover:text-crate-text">
                    View Cypher query
                  </summary>
                  <pre className="mt-2 text-xs text-crate-muted overflow-x-auto">
                    {msg.cypher}
                  </pre>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="rounded-lg p-4 bg-crate-surface border border-crate-border">
            <p className="text-sm text-crate-accent animate-pulse">Thinking...</p>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your collection..."
          className="flex-1 px-3 py-2 bg-crate-surface border border-crate-border rounded text-sm focus:outline-none focus:border-crate-accent"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 bg-crate-accent text-black text-sm font-medium rounded hover:bg-amber-400 disabled:opacity-50 transition-colors"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
