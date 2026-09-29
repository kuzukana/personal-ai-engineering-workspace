"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  EvaluationResult,
  ModelSummary,
  ResearchItem,
  RunDetail,
  RunEvent,
  createResearch,
  eventsUrl,
  getEvaluations,
  getResearchByRun,
  getRun,
  listModels,
} from "../../lib/api";

const TERMINAL_EVENTS = ["run.completed", "run.failed", "run.cancelled"];
const KNOWN_EVENTS = [
  "run.created",
  "run.started",
  "run.completed",
  "run.failed",
  "run.cancelled",
  "agent.started",
  "agent.step.started",
  "agent.step.completed",
  "agent.step.failed",
  "agent.completed",
  "model.started",
  "model.text.delta",
  "model.usage",
  "model.completed",
  "model.failed",
  "tool.started",
  "tool.completed",
  "tool.failed",
  "evaluation.started",
  "evaluation.metric.completed",
  "evaluation.completed",
  "evaluation.failed",
];

function eventLabel(event: RunEvent): string {
  const payload = event.payload;
  if (event.type.startsWith("agent.step.")) {
    return String(payload.step_name ?? payload.step_key ?? event.type);
  }
  if (event.type.startsWith("tool.")) {
    return String(payload.tool_name ?? event.type);
  }
  if (event.type.startsWith("model.")) {
    return String(payload.model ?? payload.model_id ?? event.type);
  }
  if (event.type === "evaluation.metric.completed") {
    return String(payload.metric_name ?? event.type);
  }
  return event.type;
}

export default function ResearchPage() {
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [selectedModelId, setSelectedModelId] = useState("");
  const [query, setQuery] = useState("Compare LangGraph and PydanticAI.");
  const [runId, setRunId] = useState<string | null>(null);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [research, setResearch] = useState<ResearchItem | null>(null);
  const [evaluations, setEvaluations] = useState<EvaluationResult[]>([]);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let active = true;
    listModels()
      .then((items) => {
        if (!active) return;
        setModels(items);
        setSelectedModelId((current) => current || items[0]?.id || "");
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Failed to load models.");
        }
      });
    return () => {
      active = false;
      sourceRef.current?.close();
    };
  }, []);

  const selectedModel = useMemo(
    () => models.find((model) => model.id === selectedModelId) ?? null,
    [models, selectedModelId],
  );

  async function loadFinalState(id: string) {
    const [runResult, evaluationResult] = await Promise.all([
      getRun(id),
      getEvaluations(id),
    ]);
    setRun(runResult);
    setEvaluations(evaluationResult);

    if (runResult.status === "COMPLETED") {
      try {
        setResearch(await getResearchByRun(id));
      } catch {
        setResearch(null);
      }
    }
  }

  function connectEvents(id: string, path: string) {
    sourceRef.current?.close();
    const source = new EventSource(eventsUrl(path));
    sourceRef.current = source;

    for (const type of KNOWN_EVENTS) {
      source.addEventListener(type, (message) => {
        const event = JSON.parse((message as MessageEvent<string>).data) as RunEvent;
        setEvents((current) => {
          if (current.some((item) => item.id === event.id)) {
            return current;
          }
          return [...current, event].sort((a, b) => a.sequence - b.sequence);
        });

        if (TERMINAL_EVENTS.includes(type)) {
          source.close();
          sourceRef.current = null;
          void loadFinalState(id).catch((reason: unknown) => {
            setError(
              reason instanceof Error ? reason.message : "Failed to load final run state.",
            );
          });
        }
      });
    }

    source.onerror = () => {
      if (source.readyState === EventSource.CLOSED) {
        return;
      }
    };
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim() || !selectedModelId) return;

    sourceRef.current?.close();
    setSubmitting(true);
    setError(null);
    setRun(null);
    setResearch(null);
    setEvaluations([]);
    setEvents([]);

    try {
      const created = await createResearch(query.trim(), selectedModelId);
      setRunId(created.run_id);
      setRun({
        id: created.run_id,
        status: created.status,
        input_text: query.trim(),
        output_text: null,
        structured_output: null,
        latency_ms: null,
        error_code: null,
      });
      connectEvents(created.run_id, created.events_url);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Failed to start research.");
    } finally {
      setSubmitting(false);
    }
  }

  const report = research?.structured_result;

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <Link className="back-link" href="/">
            ← Workspace
          </Link>
          <p className="eyebrow">Research Agent · V0.1</p>
          <h1 className="workspace-title">Research with a visible execution trace.</h1>
          <p className="lead">
            Choose a registered model, submit a task, and inspect the Agent, Tool,
            Model and Evaluation events as they happen.
          </p>
        </div>
      </header>

      <section className="workspace-grid">
        <div className="panel composer-panel">
          <h2>New research</h2>
          <form onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="research-query">
              Research task
            </label>
            <textarea
              id="research-query"
              className="research-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={7}
            />

            <label className="field-label" htmlFor="model">
              Model
            </label>
            <select
              id="model"
              className="model-select"
              value={selectedModelId}
              onChange={(event) => setSelectedModelId(event.target.value)}
              disabled={!models.length || submitting}
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.display_name} · {model.provider}
                </option>
              ))}
            </select>

            {selectedModel && (
              <div className="model-meta">
                <span>{selectedModel.capabilities.streaming ? "Streaming" : "No stream"}</span>
                <span>{selectedModel.capabilities.tools ? "Tools" : "No tools"}</span>
                <span>
                  {selectedModel.capabilities.structured_output
                    ? "Structured output"
                    : "Text output"}
                </span>
              </div>
            )}

            <button
              className="primary-button"
              disabled={submitting || !selectedModelId || !query.trim()}
              type="submit"
            >
              {submitting ? "Starting…" : "Start research"}
            </button>
          </form>

          {error && <div className="error-box">{error}</div>}
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Live timeline</h2>
            {run && <span className={`status-pill status-${run.status.toLowerCase()}`}>{run.status}</span>}
          </div>

          {!runId && <p className="empty-state">Start a research task to create a Run.</p>}

          {runId && (
            <>
              <p className="run-id">Run {runId}</p>
              <ol className="timeline-list">
                {events.map((event) => (
                  <li key={event.id} className="timeline-item">
                    <span className="timeline-sequence">{event.sequence}</span>
                    <div>
                      <strong>{event.type}</strong>
                      <p>{eventLabel(event)}</p>
                    </div>
                  </li>
                ))}
              </ol>
              {!events.length && <p className="empty-state">Waiting for events…</p>}
            </>
          )}
        </div>
      </section>

      {(research || run?.status === "FAILED") && (
        <section className="panel result-panel">
          <div className="panel-heading">
            <h2>{research?.title ?? "Run result"}</h2>
            {run?.latency_ms != null && <span>{run.latency_ms} ms</span>}
          </div>

          {run?.status === "FAILED" && (
            <div className="error-box">
              Run failed{run.error_code ? ` · ${run.error_code}` : ""}.
            </div>
          )}

          {report && (
            <>
              <p className="report-summary">{report.summary ?? research?.summary}</p>

              {!!report.key_findings?.length && (
                <div className="result-section">
                  <h3>Key findings</h3>
                  <ul>
                    {report.key_findings.map((finding, index) => (
                      <li key={`${finding}-${index}`}>{finding}</li>
                    ))}
                  </ul>
                </div>
              )}

              {!!report.sources?.length && (
                <div className="result-section">
                  <h3>Sources</h3>
                  <div className="source-list">
                    {report.sources.map((source, index) => (
                      <a
                        className="source-card"
                        href={source.url}
                        key={`${source.url}-${index}`}
                        rel="noreferrer"
                        target="_blank"
                      >
                        <strong>{source.title || source.url}</strong>
                        {source.snippet && <span>{source.snippet}</span>}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {!!report.next_actions?.length && (
                <div className="result-section">
                  <h3>Next actions</h3>
                  <ul>
                    {report.next_actions.map((action, index) => (
                      <li key={`${action}-${index}`}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {!!evaluations.length && (
            <div className="result-section">
              <h3>Evaluation</h3>
              <div className="evaluation-grid">
                {evaluations.map((evaluation) => (
                  <div className="evaluation-card" key={evaluation.metric_name}>
                    <span>{evaluation.metric_name}</span>
                    <strong>{evaluation.status}</strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
