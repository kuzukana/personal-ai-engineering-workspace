"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  CapabilityItem,
  EvidenceItem,
  createEvidence,
  createTechnology,
  linkCapabilityEvidence,
  listCapabilities,
  listEvidences,
  updateCapability,
} from "../../lib/api";

function CapabilityCard({
  item,
  evidences,
  onRefresh,
}: {
  item: CapabilityItem;
  evidences: EvidenceItem[];
  onRefresh: () => Promise<void>;
}) {
  const current = item.capability;
  const [level, setLevel] = useState(current?.level ?? 0);
  const [reason, setReason] = useState(current?.reason ?? "");
  const [nextTarget, setNextTarget] = useState(current?.next_target_level ?? 1);
  const [nextAction, setNextAction] = useState(current?.next_action ?? "");
  const [evidenceId, setEvidenceId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function save() {
    const result = await updateCapability(item.technology.id, {
      level,
      reason: reason || null,
      next_target_level: nextTarget,
      next_action: nextAction || null,
    });
    setMessage("Capability saved.");
    if (!evidenceId && result.capability?.id) {
      await onRefresh();
    }
  }

  async function linkEvidence() {
    if (!current?.id || !evidenceId) return;
    await linkCapabilityEvidence(current.id, evidenceId);
    setMessage("Evidence linked.");
  }

  return (
    <article className="capability-card">
      <div className="panel-heading">
        <div>
          <h2>{item.technology.name}</h2>
          <span className="muted-line">{item.technology.category || "Uncategorized"}</span>
        </div>
        <span className="capability-level">L{current?.level ?? 0}</span>
      </div>

      <div className="form-grid">
        <label>
          <span>Level</span>
          <select
            className="model-select"
            onChange={(event) => setLevel(Number(event.target.value))}
            value={level}
          >
            {[0, 1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Next target</span>
          <select
            className="model-select"
            onChange={(event) => setNextTarget(Number(event.target.value))}
            value={nextTarget}
          >
            {[0, 1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="field-label">
        Why this level?
        <textarea
          className="research-input"
          onChange={(event) => setReason(event.target.value)}
          rows={3}
          value={reason}
        />
      </label>

      <label className="field-label">
        Next action
        <textarea
          className="research-input"
          onChange={(event) => setNextAction(event.target.value)}
          rows={2}
          value={nextAction}
        />
      </label>

      <button className="secondary-button" onClick={() => void save()} type="button">
        Save capability
      </button>

      <div className="capability-evidence-row">
        <select
          className="model-select"
          disabled={!current?.id || !evidences.length}
          onChange={(event) => setEvidenceId(event.target.value)}
          value={evidenceId}
        >
          <option value="">Link evidence…</option>
          {evidences.map((evidence) => (
            <option key={evidence.id} value={evidence.id}>
              {evidence.title}
            </option>
          ))}
        </select>
        <button
          className="secondary-button"
          disabled={!current?.id || !evidenceId}
          onClick={() => void linkEvidence()}
          type="button"
        >
          Link
        </button>
      </div>

      {message && <div className="success-box">{message}</div>}
    </article>
  );
}

export default function CapabilitiesPage() {
  const [items, setItems] = useState<CapabilityItem[]>([]);
  const [evidences, setEvidences] = useState<EvidenceItem[]>([]);
  const [technologyName, setTechnologyName] = useState("");
  const [technologyCategory, setTechnologyCategory] = useState("");
  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [evidenceType, setEvidenceType] = useState("PROJECT");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const [capabilityItems, evidenceItems] = await Promise.all([
      listCapabilities(),
      listEvidences(),
    ]);
    setItems(capabilityItems);
    setEvidences(evidenceItems);
  }

  useEffect(() => {
    void refresh().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Failed to load capabilities.");
    });
  }, []);

  async function addTechnology(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!technologyName.trim()) return;
    await createTechnology({
      name: technologyName.trim(),
      category: technologyCategory.trim() || null,
      description: null,
    });
    setTechnologyName("");
    setTechnologyCategory("");
    await refresh();
  }

  async function addEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!evidenceTitle.trim()) return;
    await createEvidence({
      title: evidenceTitle.trim(),
      evidence_type: evidenceType,
      description: null,
      url: evidenceUrl.trim() || null,
    });
    setEvidenceTitle("");
    setEvidenceUrl("");
    await refresh();
  }

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <Link className="back-link" href="/">
            ← Workspace
          </Link>
          <p className="eyebrow">Capability + Evidence · V0.1</p>
          <h1 className="workspace-title">Track what you can prove, not just what you read.</h1>
          <p className="lead">
            Capability levels are backed by reasons, next actions and explicit evidence.
          </p>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      <section className="workspace-grid capability-layout">
        <div className="panel">
          <h2>Add technology</h2>
          <form onSubmit={(event) => void addTechnology(event)}>
            <label className="field-label">
              Name
              <input
                className="search-input"
                onChange={(event) => setTechnologyName(event.target.value)}
                value={technologyName}
              />
            </label>
            <label className="field-label">
              Category
              <input
                className="search-input"
                onChange={(event) => setTechnologyCategory(event.target.value)}
                placeholder="Agent, Backend, ML…"
                value={technologyCategory}
              />
            </label>
            <button className="primary-button" type="submit">
              Add technology
            </button>
          </form>
        </div>

        <div className="panel">
          <h2>Add evidence</h2>
          <form onSubmit={(event) => void addEvidence(event)}>
            <label className="field-label">
              Title
              <input
                className="search-input"
                onChange={(event) => setEvidenceTitle(event.target.value)}
                value={evidenceTitle}
              />
            </label>
            <label className="field-label">
              Type
              <select
                className="model-select"
                onChange={(event) => setEvidenceType(event.target.value)}
                value={evidenceType}
              >
                <option value="PROJECT">Project</option>
                <option value="RESEARCH">Research</option>
                <option value="CODE">Code</option>
                <option value="ARTICLE">Article</option>
                <option value="OTHER">Other</option>
              </select>
            </label>
            <label className="field-label">
              URL
              <input
                className="search-input"
                onChange={(event) => setEvidenceUrl(event.target.value)}
                value={evidenceUrl}
              />
            </label>
            <button className="primary-button" type="submit">
              Add evidence
            </button>
          </form>
        </div>
      </section>

      <section className="capability-list">
        {items.map((item) => (
          <CapabilityCard
            evidences={evidences}
            item={item}
            key={item.technology.id}
            onRefresh={refresh}
          />
        ))}
        {!items.length && (
          <div className="panel empty-state">Add your first technology to start tracking.</div>
        )}
      </section>
    </main>
  );
}
