"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { KnowledgeItem, listKnowledge } from "../../lib/api";

export default function KnowledgePage() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load(search?: string) {
    setLoading(true);
    setError(null);
    try {
      setItems(await listKnowledge(search));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Failed to load knowledge.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <Link className="back-link" href="/">
            ← Workspace
          </Link>
          <p className="eyebrow">Knowledge · V0.1</p>
          <h1 className="workspace-title">Reusable research, not disposable answers.</h1>
          <p className="lead">
            Promote useful Research runs into durable Knowledge items and revisit them later.
          </p>
        </div>
      </header>

      <section className="panel">
        <form
          className="search-row"
          onSubmit={(event) => {
            event.preventDefault();
            void load(query);
          }}
        >
          <input
            className="search-input"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search knowledge…"
            value={query}
          />
          <button className="secondary-button" type="submit">
            Search
          </button>
        </form>

        {error && <div className="error-box">{error}</div>}
        {loading && <p className="empty-state">Loading…</p>}

        {!loading && !items.length && (
          <p className="empty-state">
            No Knowledge yet. Run a Research task and save the result.
          </p>
        )}

        <div className="knowledge-list">
          {items.map((item) => (
            <Link className="knowledge-card" href={`/knowledge/${item.id}`} key={item.id}>
              <div className="panel-heading">
                <h2>{item.title}</h2>
                <span className="mini-status">{item.knowledge_type}</span>
              </div>
              <p>{item.summary || "No summary"}</p>
              <span className="muted-line">
                Updated {new Date(item.updated_at).toLocaleString()}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
