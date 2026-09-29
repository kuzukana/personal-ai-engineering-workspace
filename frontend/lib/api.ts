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
  task_type: string | null;
  model_id: string;
  input_text: string;
  output_text: string | null;
  structured_output: Record<string, unknown> | null;
  latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost: number | null;
  currency: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
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

export type CapabilityItem = {
  technology: {
    id: string;
    name: string;
    slug: string;
    category: string | null;
    description: string | null;
  };
  capability: {
    id: string;
    level: number;
    reason: string | null;
    next_target_level: number | null;
    next_action: string | null;
    updated_at: string;
  } | null;
};

export type EvidenceItem = {
  id: string;
  title: string;
  evidence_type: string;
  description: string | null;
  url: string | null;
  metadata: Record<string, unknown>;
  technologies: Array<{
    id: string;
    name: string;
    slug: string;
    category: string | null;
  }>;
  created_at: string;
  updated_at: string;
};

export type KnowledgeItem = {
  id: string;
  knowledge_type: string;
  title: string;
  summary: string | null;
  content_markdown: string | null;
  source_research_id: string | null;
  status: string;
  metadata: Record<string, unknown>;
  technologies: Array<{
    id: string;
    name: string;
    slug: string;
    category: string | null;
  }>;
  created_at: string;
  updated_at: string;
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

export async function listRuns(): Promise<RunDetail[]> {
  const response = await jsonRequest<{ data: RunDetail[] }>("/api/v1/runs");
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

export async function getEventHistory(runId: string): Promise<RunEvent[]> {
  const response = await jsonRequest<{ data: RunEvent[] }>(
    `/api/v1/runs/${runId}/events/history`,
  );
  return response.data;
}

export async function getEvaluations(runId: string): Promise<EvaluationResult[]> {
  const response = await jsonRequest<{ data: EvaluationResult[] }>(
    `/api/v1/runs/${runId}/evaluations`,
  );
  return response.data;
}

export async function saveResearchToKnowledge(runId: string): Promise<KnowledgeItem> {
  const response = await jsonRequest<{ data: KnowledgeItem }>(
    `/api/v1/knowledge/from-research/${runId}`,
    { method: "POST" },
  );
  return response.data;
}

export async function listKnowledge(query?: string): Promise<KnowledgeItem[]> {
  const suffix = query?.trim()
    ? `?q=${encodeURIComponent(query.trim())}`
    : "";
  const response = await jsonRequest<{ data: KnowledgeItem[] }>(
    `/api/v1/knowledge${suffix}`,
  );
  return response.data;
}

export async function getKnowledge(id: string): Promise<KnowledgeItem> {
  const response = await jsonRequest<{ data: KnowledgeItem }>(
    `/api/v1/knowledge/${id}`,
  );
  return response.data;
}

export async function listCapabilities(): Promise<CapabilityItem[]> {
  const response = await jsonRequest<{ data: CapabilityItem[] }>(
    "/api/v1/capabilities",
  );
  return response.data;
}

export async function createTechnology(input: {
  name: string;
  category: string | null;
  description: string | null;
}): Promise<CapabilityItem> {
  const response = await jsonRequest<{ data: CapabilityItem }>(
    "/api/v1/capabilities/technologies",
    { method: "POST", body: JSON.stringify(input) },
  );
  return response.data;
}

export async function updateCapability(
  technologyId: string,
  input: {
    level: number;
    reason: string | null;
    next_target_level: number | null;
    next_action: string | null;
  },
): Promise<CapabilityItem> {
  const response = await jsonRequest<{ data: CapabilityItem }>(
    `/api/v1/capabilities/technologies/${technologyId}`,
    { method: "PUT", body: JSON.stringify(input) },
  );
  return response.data;
}

export async function listEvidences(): Promise<EvidenceItem[]> {
  const response = await jsonRequest<{ data: EvidenceItem[] }>(
    "/api/v1/capabilities/evidences",
  );
  return response.data;
}

export async function createEvidence(input: {
  title: string;
  evidence_type: string;
  description: string | null;
  url: string | null;
}): Promise<EvidenceItem> {
  const response = await jsonRequest<{ data: EvidenceItem }>(
    "/api/v1/capabilities/evidences",
    { method: "POST", body: JSON.stringify(input) },
  );
  return response.data;
}

export async function linkCapabilityEvidence(
  capabilityId: string,
  evidenceId: string,
): Promise<void> {
  await jsonRequest(
    `/api/v1/capabilities/${capabilityId}/evidences/${evidenceId}`,
    { method: "POST" },
  );
}

export function eventsUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}
