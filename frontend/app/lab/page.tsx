"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RunDetail, listRuns } from "../../lib/api";

export default function AgentLabPage() {
  const [runs, setRuns] = useState<RunDetail[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    listRuns(offset)
      .then((data) => { if (active) setRuns(data); })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Failed to load runs.");
      }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [offset]);

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <Link className="back-link" href="/">
            ← Workspace
          </Link>
          <p className="eyebrow">Agent Lab · V0.1</p>
          <h1 className="workspace-title">Inspect how the Agent actually worked.</h1>
          <p className="lead">
            Runs, model calls, tools, events, latency and evaluation stay visible after the task ends.
          </p>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      <section className="panel">
        <div className="panel-heading">
          <h2>Runs</h2>
          <span className="mini-status">{runs.length} loaded</span>
        </div>

        <div className="result-actions">
          <button type="button" disabled={loading || offset === 0} onClick={() => setOffset(offset - 50)}>Previous</button>
          <span>Page {offset / 50 + 1}</span>
          <button type="button" disabled={loading || runs.length < 50} onClick={() => setOffset(offset + 50)}>Next</button>
        </div>
        <div className="run-list">
          {runs.map((run) => (
            <Link className="run-card" href={`/lab/${run.id}`} key={run.id}>
              <div className="panel-heading">
                <strong>{run.input_text}</strong>
                <span className={`status-pill status-${run.status.toLowerCase()}`}>
                  {run.status}
                </span>
              </div>
              <div className="run-metrics">
                <span>{run.task_type || "task"}</span>
                <span>{run.latency_ms != null ? `${run.latency_ms} ms` : "—"}</span>
                <span>
                  {run.input_tokens != null || run.output_tokens != null
                    ? `${run.input_tokens ?? 0} in / ${run.output_tokens ?? 0} out`
                    : "tokens —"}
                </span>
              </div>
              <span className="muted-line">
                {new Date(run.created_at).toLocaleString()}
              </span>
            </Link>
          ))}
          {!runs.length && <p className="empty-state">No runs yet.</p>}
        </div>
      </section>
    </main>
  );
}
