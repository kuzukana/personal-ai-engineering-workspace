"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { indexKnowledgeBatch, retrieveKnowledge, RetrievalResult } from "../../lib/api";

export default function RetrievalPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<RetrievalResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const revision = useRef(0);
  const active = useRef(true);
  const indexLock = useRef(false);

  useEffect(() => {
    active.current = true;
    return () => { active.current = false; revision.current += 1; };
  }, []);

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    const current = ++revision.current;
    setSearching(true);
    setError(null);
    try {
      const found = await retrieveKnowledge(query.trim());
      if (active.current && current === revision.current) setResult(found);
    } catch (reason) {
      if (active.current && current === revision.current)
        setError(reason instanceof Error ? reason.message : "Search failed.");
    } finally {
      if (active.current && current === revision.current) setSearching(false);
    }
  }

  async function index() {
    if (indexLock.current) return;
    indexLock.current = true;
    setIndexing(true);
    setError(null);
    setMessage(null);
    let cursor: string | null = null;
    let count = 0;
    let failed = 0;
    try {
      do {
        const batch = await indexKnowledgeBatch(cursor);
        count += batch.results.length;
        failed += batch.errors.length;
        cursor = batch.next_cursor;
        if (!active.current) return;
        setMessage(`${count} Knowledge items indexed or up to date. ${failed} skipped.`);
      } while (cursor);
      if (failed) setError("Some items could not be indexed. Check their size or retry after edits finish.");
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : "Indexing failed.");
    } finally {
      indexLock.current = false;
      if (active.current) setIndexing(false);
    }
  }

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <Link className="back-link" href="/knowledge">← Knowledge</Link>
          <p className="eyebrow">Knowledge retrieval · V0.2</p>
          <h1 className="workspace-title">Find evidence you can trace.</h1>
          <p className="lead">Search saved Knowledge and inspect the exact supporting excerpts.</p>
        </div>
      </header>
      <section className="panel">
        <p>Index Knowledge before your first search or after edits. When a live embedding provider is configured,
          indexing sends Knowledge text to that provider and may incur charges. The default demo runs locally.</p>
        <button className="secondary-button" disabled={indexing} onClick={() => void index()} type="button">
          {indexing ? "Indexing…" : "Index Knowledge"}
        </button>
        {message && <p role="status">{message}</p>}
        <form className="search-row" onSubmit={(event) => void search(event)}>
          <input className="search-input" aria-label="Search saved evidence" value={query} maxLength={2000}
            onChange={(event) => setQuery(event.target.value)} placeholder="What evidence do you need?" />
          <button className="primary-button" disabled={!query.trim()} type="submit">Search evidence</button>
        </form>
        {searching && <p role="status">Searching…</p>}
        {error && <div role="alert" className="error-box">{error}</div>}
      </section>
      {result && <section className="panel result-panel">
        <p className="muted-line">{result.mode === "demo" ? "Demo: lexical approximation; not semantic understanding." : "Semantic retrieval"}
          {` · ${result.indexed_documents} indexed documents`}</p>
        {result.stale_documents > 0 && <p>{result.stale_documents} outdated documents were excluded. Reindex to include edits.</p>}
        {!result.hits.length && <p>No matching evidence. Index your Knowledge or try a different query.</p>}
        {result.hits.map((hit) => <article className="knowledge-card" key={`${hit.knowledge_id}-${hit.ordinal}`}>
          <Link href={`/knowledge/${hit.knowledge_id}`}><h2>[{hit.citation}] {hit.title}</h2></Link>
          <p>{hit.text}</p>
          <span className="muted-line">{`Excerpt ${hit.ordinal + 1} · characters ${hit.start_offset}–${hit.end_offset} · similarity ${hit.score.toFixed(3)}`}</span>
        </article>)}
        {!!result.context && <details><summary>Evidence context with citations</summary><pre style={{ whiteSpace: "pre-wrap" }}>{result.context}</pre></details>}
      </section>}
    </main>
  );
}
