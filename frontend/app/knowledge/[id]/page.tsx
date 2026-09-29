"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { KnowledgeItem, getKnowledge } from "../../../lib/api";

export default function KnowledgeDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<KnowledgeItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    getKnowledge(params.id)
      .then(setItem)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Failed to load knowledge.");
      });
  }, [params.id]);

  return (
    <main className="workspace-shell">
      <Link className="back-link" href="/knowledge">
        ← Knowledge
      </Link>

      {error && <div className="error-box">{error}</div>}
      {!item && !error && <p className="empty-state">Loading…</p>}

      {item && (
        <article className="panel result-panel">
          <div className="panel-heading">
            <h2>{item.title}</h2>
            <span className="mini-status">{item.knowledge_type}</span>
          </div>
          <p className="report-summary">{item.summary}</p>
          {!!item.technologies.length && (
            <div className="model-meta">
              {item.technologies.map((technology) => (
                <span key={technology.id}>{technology.name}</span>
              ))}
            </div>
          )}
          <div className="knowledge-content">
            <pre>{item.content_markdown || "No content."}</pre>
          </div>
        </article>
      )}
    </main>
  );
}
