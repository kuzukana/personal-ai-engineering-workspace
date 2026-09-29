export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type HealthResponse = { status: string };

export type ModelCapabilities = {
  streaming: boolean;
  tools: boolean;
  parallel_tools?: boolean;
  structured_output: boolean;
  vision?: boolean;
  reasoning?: boolean;
  system_prompt?: boolean;
  context_window?: number | null;
  max_output_tokens?: number | null;
};

export type ModelSummary = {
  id: string;
  provider: string;
  model_key: string;
  display_name: string;
  capabilities: ModelCapabilities;
};

export type RunEvent = {
  id: string;
  run_id: string;
  sequence: number;
  type: string;
  timestamp: string;
  source?: string;
  payload: Record<string, unknown>;
};

export type RunDetail = {
  id: string;
  status: string;
  input_text: string;
  output_text: string | null;
  structured_output: Record<string, unknown> | null;
  latency_ms: number | null;
  error_code: string | null;
};

export type ResearchSource = {
  url: string;
  title?: string | null;
  snippet?: string | null;
  source_type?: string | null;
};

export type ResearchReport = {
  title?: string;
  summary?: string;
  key_findings?: string[];
  sources?: ResearchSource[];
  open_questions?: string[];
  next_actions?: string[];
};

export type ResearchItem = {
  id: string;
  run_id: string | null;
  title: string;
  query: string;
  summary: string | null;
  status: string;
  structured_result: ResearchReport | null;
};

export type EvaluationResult = {
  metric_name: string;
  evaluation_type: string;
  status: string;
  evaluator_version: string;
  evidence: Record<string, unknown> | null;
};

async function jsonRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return jsonRequest<HealthResponse>("/health");
}

export async function listModels(): Promise<ModelSummary[]> {
  const response = await jsonRequest<{ data: ModelSummary[] }>("/api/v1/models");
  return response.data;
}

export async function createResearch(
  query: string,
  modelId: string,
): Promise<{ run_id: string; status: string; events_url: string }> {
  const response = await jsonRequest<{
    data: { run_id: string; status: string; events_url: string };
  }>("/api/v1/research", {
    method: "POST",
    body: JSON.stringify({ query, model_id: modelId }),
  });
  return response.data;
}

export async function getRun(runId: string): Promise<RunDetail> {
  const response = await jsonRequest<{ data: RunDetail }>(`/api/v1/runs/${runId}`);
  return response.data;
}

export async function getResearchByRun(runId: string): Promise<ResearchItem> {
  const response = await jsonRequest<{ data: ResearchItem }>(
    `/api/v1/research/${runId}`,
  );
  return response.data;
}

export async function getEvaluations(runId: string): Promise<EvaluationResult[]> {
  const response = await jsonRequest<{ data: EvaluationResult[] }>(
    `/api/v1/runs/${runId}/evaluations`,
  );
  return response.data;
}

export function eventsUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}
