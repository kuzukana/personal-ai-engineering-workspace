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
  cancelRun,
  eventsUrl,
  getEvaluations,
  getResearchByRun,
  getRun,
  listModels,
  saveResearchToKnowledge,
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
  const [savingKnowledge, setSavingKnowledge] = useState(false);
  const [knowledgeMessage, setKnowledgeMessage] = useState<string | null>(null);
  const generationRef = useRef(0);
  const loadRevisionRef = useRef(0);
  const [cancelling, setCancelling] = useState(false);
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
      generationRef.current += 1;
      sourceRef.current?.close();
    };
  }, []);

  const selectedModel = useMemo(
    () => models.find((model) => model.id === selectedModelId) ?? null,
    [models, selectedModelId],
  );

  async function loadFinalState(id: string, generation: number) {
    const revision = ++loadRevisionRef.current;
    const [runResult, evaluationResult] = await Promise.all([getRun(id), getEvaluations(id)]);
    const researchResult = runResult.status === "COMPLETED" ? await getResearchByRun(id) : null;
    if (generation !== generationRef.current || revision !== loadRevisionRef.current) return;
    setRun((current) => {
      const order: Record<string, number> = { PENDING: 0, RUNNING: 1, CANCELLATION_REQUESTED: 2,
        COMPLETED: 3, FAILED: 3, CANCELLED: 3 };
      return current?.id === id && order[current.status] > order[runResult.status] ? current : runResult;
    });
    setEvaluations(evaluationResult);
    if (researchResult) setResearch(researchResult);
    if (["COMPLETED", "FAILED", "CANCELLED"].includes(runResult.status)) {
      sourceRef.current?.close();
      sourceRef.current = null;
    }
  }

  function connectEvents(id: string, path: string, generation: number) {
    sourceRef.current?.close();
    const source = new EventSource(eventsUrl(path));
    sourceRef.current = source;
    for (const type of KNOWN_EVENTS) {
      source.addEventListener(type, (message) => {
        if (generation !== generationRef.current) return;
        const event = JSON.parse((message as MessageEvent<string>).data) as RunEvent;
        if (event.run_id !== id) return;
        setEvents((current) => current.some((item) => item.id === event.id) ? current :
          [...current, event].sort((a, b) => a.sequence - b.sequence));
        if (type === "run.started") setRun((current) => current?.id === id ?
          { ...current, status: current.status === "CANCELLATION_REQUESTED" ? current.status : "RUNNING" } : current);
        if (TERMINAL_EVENTS.includes(type)) {
          setRun((current) => current?.id === id ? { ...current, status: type.slice(4).toUpperCase() } : current);
          source.close();
          sourceRef.current = null;
          void loadFinalState(id, generation).catch((reason: unknown) => {
            if (generation === generationRef.current) setError(
              reason instanceof Error ? reason.message : "Failed to load final run state.");
          });
        }
      });
    }
    source.onerror = () => {
      if (generation !== generationRef.current) return;
      void loadFinalState(id, generation).catch(() => {
        if (generation === generationRef.current) setError("Connection interrupted. Retrying…");
      });
    };
  }

  useEffect(() => {
    if (!runId || (run && ["COMPLETED", "FAILED", "CANCELLED"].includes(run.status))) return;
    const generation = generationRef.current;
    let pending = false;
    const timer = setInterval(() => {
      if (pending || generation !== generationRef.current) return;
      pending = true;
      void loadFinalState(runId, generation).catch(() => {
        if (generation === generationRef.current) setError("Unable to refresh run. Retrying…");
      }).finally(() => { pending = false; });
    }, 5000);
    return () => clearInterval(timer);
  }, [runId, run?.status]);

  async function handleCancel() {
    if (!runId || cancelling) return;
    const generation = generationRef.current;
    setCancelling(true);
    setError(null);
    try {
      await cancelRun(runId);
      if (generation === generationRef.current) setRun((current) => current &&
        !["COMPLETED", "FAILED", "CANCELLED"].includes(current.status) ?
        { ...current, status: "CANCELLATION_REQUESTED" } : current);
    } catch (reason) {
      if (generation === generationRef.current) setError(reason instanceof Error ? reason.message : "Cancel failed.");
    } finally {
      if (generation === generationRef.current) setCancelling(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim() || !selectedModelId) return;

    const generation = ++generationRef.current;
    sourceRef.current?.close();
    setRunId(null);
    setCancelling(false);
    setSavingKnowledge(false);
    setSubmitting(true);
    setError(null);
    setRun(null);
    setResearch(null);
    setEvaluations([]);
    setEvents([]);
    setKnowledgeMessage(null);

    try {
      const created = await createResearch(query.trim(), selectedModelId);
      if (generation !== generationRef.current) return;
      setRunId(created.run_id);
      setRun({
        id: created.run_id,
        status: created.status,
        task_type: "research",
        model_id: selectedModelId,
        input_text: query.trim(),
        output_text: null,
        structured_output: null,
        latency_ms: null,
        input_tokens: null,
        output_tokens: null,
        estimated_cost: null,
        currency: null,
        error_code: null,
        error_message: null,
        created_at: new Date().toISOString(),
        started_at: null,
        completed_at: null,
      });
      connectEvents(created.run_id, created.events_url, generation);
    } catch (reason: unknown) {
      if (generation === generationRef.current) setError(reason instanceof Error ? reason.message : "Failed to start research.");
    } finally {
      if (generation === generationRef.current) setSubmitting(false);
    }
  }

  async function handleSaveKnowledge() {
    if (!runId || research?.run_id !== runId) return;
    const generation = generationRef.current;
    setError(null);
    setSavingKnowledge(true);
    setKnowledgeMessage(null);
    try {
      const item = await saveResearchToKnowledge(runId);
      if (generation !== generationRef.current) return;
      setKnowledgeMessage(`Saved to Knowledge: ${item.title}`);
    } catch (reason: unknown) {
      if (generation === generationRef.current) setError(reason instanceof Error ? reason.message : "Failed to save Knowledge.");
    } finally {
      if (generation === generationRef.current) setSavingKnowledge(false);
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
            {run && !["COMPLETED", "FAILED", "CANCELLED"].includes(run.status) && (
              <button className="secondary-button" type="button" disabled={cancelling || run.status === "CANCELLATION_REQUESTED"}
                onClick={() => void handleCancel()}>Cancel research</button>
            )}
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
            <div className="result-actions">
              {research && (
                <button
                  className="secondary-button"
                  disabled={savingKnowledge}
                  onClick={() => void handleSaveKnowledge()}
                  type="button"
                >
                  {savingKnowledge ? "Saving…" : "Save to Knowledge"}
                </button>
              )}
              {run?.latency_ms != null && <span>{run.latency_ms} ms</span>}
            </div>
          </div>
          {knowledgeMessage && <div className="success-box">{knowledgeMessage}</div>}

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
