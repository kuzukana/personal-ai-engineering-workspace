"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  EvaluationResult,
  RunDetail,
  RunEvent,
  getEvaluations,
  getEventHistory,
  getRun,
} from "../../../lib/api";

export default function AgentLabRunPage() {
  const params = useParams<{ id: string }>();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    Promise.all([
      getRun(params.id),
      getEventHistory(params.id),
      getEvaluations(params.id),
    ])
      .then(([runResult, eventResult, evaluationResult]) => {
        setRun(runResult);
        setEvents(eventResult);
        setEvaluations(evaluationResult);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Failed to load Run.");
      });
  }, [params.id]);

  const metrics = useMemo(() => {
    let modelCalls = 0;
    let toolCalls = 0;
    let inputTokens = 0;
    let outputTokens = 0;

    for (const event of events) {
      if (event.type === "model.started") modelCalls += 1;
      if (event.type === "tool.started") toolCalls += 1;
      if (event.type === "model.usage") {
        inputTokens += Number(event.payload.input_tokens ?? 0);
        outputTokens += Number(event.payload.output_tokens ?? 0);
      }
    }

    return { modelCalls, toolCalls, inputTokens, outputTokens };
  }, [events]);

  return (
    <main className="workspace-shell">
      <Link className="back-link" href="/lab">
        ← Agent Lab
      </Link>

      {error && <div className="error-box">{error}</div>}
      {!run && !error && <p className="empty-state">Loading…</p>}

      {run && (
        <>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Run {run.id}</p>
                <h2>{run.input_text}</h2>
              </div>
              <span className={`status-pill status-${run.status.toLowerCase()}`}>
                {run.status}
              </span>
            </div>

            <div className="lab-metric-grid">
              <div className="metric-card">
                <span>Latency</span>
                <strong>{run.latency_ms != null ? `${run.latency_ms} ms` : "—"}</strong>
              </div>
              <div className="metric-card">
                <span>Model calls</span>
                <strong>{metrics.modelCalls}</strong>
              </div>
              <div className="metric-card">
                <span>Tool calls</span>
                <strong>{metrics.toolCalls}</strong>
              </div>
              <div className="metric-card">
                <span>Tokens</span>
                <strong>{metrics.inputTokens} / {metrics.outputTokens}</strong>
              </div>
              <div className="metric-card">
                <span>Cost</span>
                <strong>
                  {run.estimated_cost != null
                    ? `${run.estimated_cost} ${run.currency ?? ""}`
                    : "—"}
                </strong>
              </div>
              <div className="metric-card">
                <span>Evaluations</span>
                <strong>{evaluations.length}</strong>
              </div>
            </div>

            {run.error_code && (
              <div className="error-box">
                {run.error_code}: {run.error_message || "Run failed."}
              </div>
            )}
          </section>

          <section className="workspace-grid lab-grid">
            <div className="panel">
              <h2>Event timeline</h2>
              <ol className="timeline-list">
                {events.map((event) => (
                  <li className="timeline-item" key={event.id}>
                    <span className="timeline-sequence">{event.sequence}</span>
                    <div>
                      <strong>{event.type}</strong>
                      <pre className="event-payload">
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="panel">
              <h2>Evaluation</h2>
              <div className="evaluation-stack">
                {evaluations.map((evaluation) => (
                  <article className="evaluation-card" key={evaluation.metric_name}>
                    <div>
                      <strong>{evaluation.metric_name}</strong>
                      <span>{evaluation.evaluation_type}</span>
                    </div>
                    <strong>{evaluation.status}</strong>
                  </article>
                ))}
                {!evaluations.length && <p className="empty-state">No evaluations.</p>}
              </div>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
