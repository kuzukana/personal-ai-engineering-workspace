"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RunDetail, listRuns } from "../../lib/api";

export default function AgentLabPage() {
  const [runs, setRuns] = useState<RunDetail[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns()
      .then(setRuns)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Failed to load runs.");
      });
  }, []);

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
