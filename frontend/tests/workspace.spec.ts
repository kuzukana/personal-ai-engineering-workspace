import { expect, test, Page } from "@playwright/test";

const model = { id: "mock", provider: "mock", display_name: "Mock", capabilities: {} };
const research = (id: string) => ({ id, run_id: id, title: `Report ${id}`,
  structured_result: { summary: `Summary ${id}`, sources: [] } });
const run = (id: string, status = "COMPLETED") => ({ id, status, input_text: id,
  created_at: new Date().toISOString(), model_id: "mock" });

async function mockEvents(page: Page) {
  await page.addInitScript(`
    window.testStreams = [];
    window.EventSource = class extends EventTarget {
      constructor(url) { super(); this.url = url; window.testStreams.push(this); }
      close() {}
    };
    window.fireRunEvent = (id, type) => {
      const stream = window.testStreams.find(s => s.url.includes('/' + id + '/events'));
      stream.dispatchEvent(new MessageEvent(type, { data: JSON.stringify({
        id: id + type, run_id: id, sequence: type === 'run.started' ? 1 : 2,
        type, payload: {}, timestamp: new Date().toISOString()
      }) }));
    };
  `);
}

async function fire(page: Page, id: string, type: string) {
  await page.evaluate(([runId, kind]) => {
    (window as unknown as { fireRunEvent: (id: string, type: string) => void }).fireRunEvent(runId, kind);
  }, [id, type]);
}

test("Research ignores a delayed old report and saves the displayed run", async ({ page }) => {
  await mockEvents(page);
  let count = 0;
  let release!: () => void;
  const delayed = new Promise<void>(resolve => { release = resolve; });
  let oldRequested!: () => void;
  const oldRequest = new Promise<void>(resolve => { oldRequested = resolve; });
  let saved = "";
  await page.route("http://127.0.0.1:8099/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = [];
    if (path.endsWith("/models")) data = [model];
    else if (path === "/api/v1/research") {
      const id = String(++count);
      data = { run_id: id, status: "PENDING", events_url: `/api/v1/runs/${id}/events` };
    } else if (path.endsWith("/evaluations")) data = [];
    else if (path.includes("/runs/")) data = run(path.split("/").at(-1)!);
    else if (path === "/api/v1/research/1") { oldRequested(); await delayed; data = research("1"); }
    else if (path === "/api/v1/research/2") data = research("2");
    else if (path.includes("from-research")) { saved = path.split("/").at(-1)!; data = { title: `Report ${saved}` }; }
    await route.fulfill({ json: { data } });
  });
  await page.goto("/research");
  await page.getByRole("button", { name: "Start research" }).click();
  await expect(page.getByText("Run 1", { exact: true })).toBeVisible();
  await fire(page, "1", "run.started");
  await expect(page.getByText("RUNNING", { exact: true })).toBeVisible();
  await fire(page, "1", "run.completed");
  await oldRequest;
  await page.getByRole("button", { name: "Start research" }).click();
  await expect(page.getByText("Run 2", { exact: true })).toBeVisible();
  await fire(page, "2", "run.completed");
  await expect(page.getByRole("heading", { name: "Report 2" })).toBeVisible();
  const oldResponse = page.waitForResponse(response => response.url().endsWith("/research/1"));
  release();
  await oldResponse;
  await expect(page.getByRole("heading", { name: "Report 1" })).toHaveCount(0);
  await page.getByRole("button", { name: "Save to Knowledge" }).click();
  await expect(page.getByText("Saved to Knowledge: Report 2")).toBeVisible();
  expect(saved).toBe("2");
});

test("Knowledge keeps latest search and renders safe Markdown citations", async ({ page }) => {
  let release!: () => void;
  const delayed = new Promise<void>(resolve => { release = resolve; });
  let requested!: () => void;
  const oldRequest = new Promise<void>(resolve => { requested = resolve; });
  const item = (id: string) => ({ id, title: id, technologies: [], knowledge_type: "RESEARCH",
    content_markdown: "# Evidence\n[Source](https://example.com)\n<script>alert(1)</script>",
    updated_at: new Date().toISOString() });
  await page.route("http://127.0.0.1:8099/**", async route => {
    const url = new URL(route.request().url());
    const query = url.searchParams.get("q");
    if (query === "old") { requested(); await delayed; }
    await route.fulfill({ json: { data: url.pathname.endsWith("/new") ? item("new") :
      query ? [item(query)] : [] } });
  });
  await page.goto("/knowledge");
  await page.getByPlaceholder("Search knowledge…").fill("old");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await oldRequest;
  await page.getByPlaceholder("Search knowledge…").fill("new");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("heading", { name: "new", exact: true })).toBeVisible();
  const oldResponse = page.waitForResponse(response => response.url().includes("q=old"));
  release();
  await oldResponse;
  await expect(page.getByRole("heading", { name: "new", exact: true })).toBeVisible();
  await page.getByRole("link", { name: /new RESEARCH/ }).click();
  await expect(page.getByRole("link", { name: "Source", exact: true })).toHaveAttribute("href", "https://example.com");
  await expect(page.locator(".knowledge-content script")).toHaveCount(0);
});

test("Capability mutations show errors and allow retry", async ({ page }) => {
  let posts = 0;
  await page.route("http://127.0.0.1:8099/**", async route => {
    if (route.request().method() === "POST") {
      posts++;
      await route.fulfill(posts === 1 ? { status: 409, json: { detail: "Technology already exists" } } :
        { json: { data: {} } });
    } else await route.fulfill({ json: { data: [] } });
  });
  await page.goto("/capabilities");
  await page.getByLabel("Name", { exact: true }).fill("Python");
  await page.getByRole("button", { name: "Add technology", exact: true }).click();
  await expect(page.getByText(/Technology already exists/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Add technology", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Add technology", exact: true }).click();
  await expect(page.getByLabel("Name", { exact: true })).toHaveValue("");
  expect(posts).toBe(2);
});


test("Retrieval ignores old responses, keeps citations, and retries indexing", async ({ page }) => {
  let release!: () => void;
  const delayed = new Promise<void>(resolve => { release = resolve; });
  let requested!: () => void;
  const oldRequest = new Promise<void>(resolve => { requested = resolve; });
  let attempts = 0;
  await page.route("http://127.0.0.1:8099/**", async route => {
    if (route.request().url().endsWith("/index")) {
      attempts++;
      await route.fulfill(attempts === 1 ? { status: 502, json: { detail: "Provider unavailable" } } :
        { json: { data: { results: [{ knowledge_id: "new" }], errors: [], next_cursor: null } } });
      return;
    }
    const query = route.request().postDataJSON().query;
    if (query === "old") { requested(); await delayed; }
    await route.fulfill({ json: { data: { mode: "demo", model: "demo", indexed_documents: 1,
      stale_documents: 1, context: `[K1] ${query} evidence`, hits: [{ knowledge_id: query,
        ordinal: 0, title: query, citation: "K1", text: `${query} evidence`, score: 0.8,
        start_offset: 0, end_offset: 12, content_hash: "hash", source_research_id: null }] } } });
  });
  await page.goto("/retrieval");
  await page.getByRole("button", { name: "Index Knowledge", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Provider unavailable" })).toBeVisible();
  await page.getByRole("button", { name: "Index Knowledge", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("1 Knowledge items");
  await page.getByRole("textbox", { name: "Search saved evidence" }).fill("old");
  await page.getByRole("button", { name: "Search evidence", exact: true }).click();
  await oldRequest;
  await page.getByRole("textbox", { name: "Search saved evidence" }).fill("new");
  await page.getByRole("button", { name: "Search evidence", exact: true }).click();
  await expect(page.getByRole("link", { name: "[K1] new", exact: true })).toHaveAttribute("href", "/knowledge/new");
  const oldResponse = page.waitForResponse(response => response.request().postDataJSON()?.query === "old");
  release();
  await oldResponse;
  await expect(page.getByRole("heading", { name: "[K1] old", exact: true })).toHaveCount(0);
  await expect(page.getByText(/outdated documents were excluded/)).toBeVisible();
  expect(attempts).toBe(2);
});
