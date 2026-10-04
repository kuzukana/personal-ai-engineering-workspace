from __future__ import annotations

from typing import TypedDict
from uuid import UUID, uuid4

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.research.schemas import ResearchReport, ResearchSourceData
from app.ai.container import model_gateway
from app.ai.schemas import ChatMessage, ModelRequest
from app.events.publisher import event_publisher
from app.runtime.run_control import run_control
from app.tools.container import tool_gateway


class ResearchState(TypedDict, total=False):
    query: str
    research_goal: str
    search_queries: list[str]
    sources: list[dict]
    selected_sources: list[dict]
    findings: list[dict]
    verification_results: list[dict]
    report: dict


class ResearchAgent:
    async def run(
        self,
        session: AsyncSession,
        run_id: UUID,
        query: str,
        model_id: str,
    ) -> ResearchReport:
        current_step: tuple[str, int] | None = None

        async def step_started(key: str, index: int) -> None:
            nonlocal current_step
            current_step = (key, index)
            run_control.raise_if_cancelled(run_id)
            await event_publisher.emit(
                session,
                run_id,
                "agent.step.started",
                "agent_runtime",
                {"step_key": key, "step_index": index},
            )

        async def step_completed(key: str, index: int) -> None:
            nonlocal current_step
            run_control.raise_if_cancelled(run_id)
            await event_publisher.emit(
                session,
                run_id,
                "agent.step.completed",
                "agent_runtime",
                {"step_key": key, "step_index": index},
            )
            current_step = None

        async def understand(state: ResearchState) -> dict:
            await step_started("understand", 1)
            update = {"research_goal": state["query"].strip()}
            await step_completed("understand", 1)
            return update

        async def plan_search(state: ResearchState) -> dict:
            await step_started("plan_search", 2)
            update = {"search_queries": [state["research_goal"]]}
            await step_completed("plan_search", 2)
            return update

        async def search(state: ResearchState) -> dict:
            await step_started("search", 3)
            tool_call_id = str(uuid4())
            await event_publisher.emit(
                session,
                run_id,
                "tool.started",
                "tool_gateway",
                {
                    "tool_call_id": tool_call_id,
                    "tool_name": "web_search",
                    "risk_level": "LOW",
                },
            )
            try:
                result = await tool_gateway.execute(
                    "web_search",
                    {"query": state["search_queries"][0]},
                )
            except Exception as exc:
                await event_publisher.emit(
                    session,
                    run_id,
                    "tool.failed",
                    "tool_gateway",
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": "web_search",
                        "error_code": type(exc).__name__.upper(),
                        "message": str(exc)[:500] or "Tool execution failed",
                        "recoverable": False,
                    },
                )
                raise
            await event_publisher.emit(
                session,
                run_id,
                "tool.completed",
                "tool_gateway",
                {
                    "tool_call_id": tool_call_id,
                    "tool_name": "web_search",
                    "result_summary": {"result_count": len(result["results"])},
                },
            )
            await step_completed("search", 3)
            return {"sources": result["results"]}

        async def select_sources(state: ResearchState) -> dict:
            await step_started("select_sources", 4)
            selected = [
                source
                for source in state["sources"]
                if source.get("url") and source.get("title")
            ][:5]
            await step_completed("select_sources", 4)
            return {"selected_sources": selected}

        async def read_sources(state: ResearchState) -> dict:
            await step_started("read_sources", 5)
            enriched: list[dict] = []
            for source in state["selected_sources"]:
                run_control.raise_if_cancelled(run_id)
                tool_call_id = str(uuid4())
                await event_publisher.emit(
                    session,
                    run_id,
                    "tool.started",
                    "tool_gateway",
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": "fetch_url",
                        "risk_level": "LOW",
                    },
                )
                try:
                    fetched = await tool_gateway.execute(
                        "fetch_url",
                        {
                            "url": source["url"],
                            "title": source["title"],
                        },
                    )
                except Exception as exc:
                    await event_publisher.emit(
                        session,
                        run_id,
                        "tool.failed",
                        "tool_gateway",
                        {
                            "tool_call_id": tool_call_id,
                            "tool_name": "fetch_url",
                            "error_code": type(exc).__name__.upper(),
                            "message": str(exc)[:500] or "Tool execution failed",
                            "recoverable": False,
                        },
                    )
                    raise
                await event_publisher.emit(
                    session,
                    run_id,
                    "tool.completed",
                    "tool_gateway",
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": "fetch_url",
                        "result_summary": {"url": source["url"]},
                    },
                )
                enriched.append(
                    {
                        **source,
                        "content": fetched.get("content"),
                    }
                )
            await step_completed("read_sources", 5)
            return {"selected_sources": enriched}

        async def extract_findings(state: ResearchState) -> dict:
            await step_started("extract_findings", 6)
            findings = []
            for source in state["selected_sources"]:
                evidence = str(source.get("content") or source.get("snippet") or "").strip()
                if not evidence:
                    continue
                findings.append(
                    {
                        "claim": evidence,
                        "evidence": evidence,
                        "source_url": source["url"],
                    }
                )
            await step_completed("extract_findings", 6)
            return {"findings": findings}

        async def verify(state: ResearchState) -> dict:
            await step_started("verify", 7)
            results = [
                {
                    **finding,
                    "status": (
                        "PARTIALLY_VERIFIED"
                        if finding.get("evidence") and finding.get("source_url")
                        else "UNVERIFIED"
                    ),
                }
                for finding in state["findings"]
            ]
            await step_completed("verify", 7)
            return {"verification_results": results}

        async def synthesize(state: ResearchState) -> dict:
            await step_started("synthesize", 8)
            model_call_id = str(uuid4())
            evidence_lines = [
                f"- [{item['status']}] {item['claim']} (source: {item['source_url']})"
                for item in state["verification_results"]
            ]
            prompt = (
                "Write a concise research summary grounded only in the evidence below. "
                "If the evidence is limited, say so explicitly.\n\n"
                f"Task: {state['query']}\n\nEvidence:\n"
                + "\n".join(evidence_lines)
            )
            await event_publisher.emit(
                session,
                run_id,
                "model.started",
                "model_gateway",
                {"model_call_id": model_call_id, "model": model_id},
            )
            try:
                response = await model_gateway.generate(
                    ModelRequest(
                        model_id=model_id,
                        messages=[ChatMessage(role="user", content=prompt)],
                    )
                )
            except Exception as exc:
                await event_publisher.emit(
                    session,
                    run_id,
                    "model.failed",
                    "model_gateway",
                    {
                        "model_call_id": model_call_id,
                        "error_code": type(exc).__name__.upper(),
                        "message": str(exc)[:500] or "Model request failed",
                        "recoverable": False,
                    },
                )
                raise
            await event_publisher.emit(
                session,
                run_id,
                "model.usage",
                "model_gateway",
                {"model_call_id": model_call_id, **response.usage.model_dump()},
            )
            await event_publisher.emit(
                session,
                run_id,
                "model.completed",
                "model_gateway",
                {
                    "model_call_id": model_call_id,
                    "finish_reason": response.finish_reason.value,
                },
            )

            verification_by_url = {
                item["source_url"]: item["status"]
                for item in state["verification_results"]
            }
            sources = [
                ResearchSourceData(
                    **source,
                    verification_status=verification_by_url.get(
                        source["url"],
                        "UNVERIFIED",
                    ),
                )
                for source in state["selected_sources"]
            ]
            report = ResearchReport(
                title=f"Research: {state['query']}",
                summary=response.content,
                key_findings=[
                    item["claim"] for item in state["verification_results"]
                ],
                sources=sources,
                open_questions=[],
                next_actions=[
                    "Review the cited evidence before promoting findings to long-term Knowledge."
                ],
            )
            await step_completed("synthesize", 8)
            return {"report": report.model_dump(mode="json")}

        graph = StateGraph(ResearchState)
        graph.add_node("understand", understand)
        graph.add_node("plan_search", plan_search)
        graph.add_node("search", search)
        graph.add_node("select_sources", select_sources)
        graph.add_node("read_sources", read_sources)
        graph.add_node("extract_findings", extract_findings)
        graph.add_node("verify", verify)
        graph.add_node("synthesize", synthesize)
        graph.add_edge(START, "understand")
        graph.add_edge("understand", "plan_search")
        graph.add_edge("plan_search", "search")
        graph.add_edge("search", "select_sources")
        graph.add_edge("select_sources", "read_sources")
        graph.add_edge("read_sources", "extract_findings")
        graph.add_edge("extract_findings", "verify")
        graph.add_edge("verify", "synthesize")
        graph.add_edge("synthesize", END)

        try:
            final_state = await graph.compile().ainvoke({"query": query})
        except Exception as exc:
            if current_step is not None:
                step_key, step_index = current_step
                await event_publisher.emit(
                    session,
                    run_id,
                    "agent.step.failed",
                    "agent_runtime",
                    {
                        "step_key": step_key,
                        "step_index": step_index,
                        "error_code": type(exc).__name__.upper(),
                        "message": str(exc)[:500] or "Agent step failed",
                        "recoverable": False,
                    },
                )
            raise
        return ResearchReport.model_validate(final_state["report"])


research_agent = ResearchAgent()
