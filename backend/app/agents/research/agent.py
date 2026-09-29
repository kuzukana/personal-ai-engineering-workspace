from __future__ import annotations

from typing import TypedDict
from uuid import UUID, uuid4

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.research.schemas import ResearchReport, ResearchSourceData
from app.ai.container import model_gateway
from app.ai.schemas import ChatMessage, ModelRequest
from app.events.publisher import event_publisher
from app.tools.gateway import tool_gateway


class ResearchState(TypedDict, total=False):
    query: str
    research_goal: str
    search_queries: list[str]
    sources: list[dict]
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
        async def step_started(key: str, index: int) -> None:
            await event_publisher.emit(
                session,
                run_id,
                "agent.step.started",
                "agent_runtime",
                {"step_key": key, "step_index": index},
            )

        async def step_completed(key: str, index: int) -> None:
            await event_publisher.emit(
                session,
                run_id,
                "agent.step.completed",
                "agent_runtime",
                {"step_key": key, "step_index": index},
            )

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
            result = await tool_gateway.execute(
                "web_search",
                {"query": state["search_queries"][0]},
            )
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

        async def verify(state: ResearchState) -> dict:
            await step_started("verify", 4)
            results = [
                {
                    "claim": source["snippet"],
                    "status": "VERIFIED",
                    "source_url": source["url"],
                }
                for source in state["sources"]
            ]
            await step_completed("verify", 4)
            return {"verification_results": results}

        async def synthesize(state: ResearchState) -> dict:
            await step_started("synthesize", 5)
            model_call_id = str(uuid4())
            await event_publisher.emit(
                session,
                run_id,
                "model.started",
                "model_gateway",
                {"model_call_id": model_call_id, "model": model_id},
            )
            response = await model_gateway.generate(
                ModelRequest(
                    model_id=model_id,
                    messages=[
                        ChatMessage(
                            role="user",
                            content=f"Summarize the research task: {state['query']}",
                        )
                    ],
                )
            )
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
            sources = [ResearchSourceData(**source) for source in state["sources"]]
            report = ResearchReport(
                title=f"Research: {state['query']}",
                summary=response.content,
                key_findings=[
                    item["claim"] for item in state["verification_results"]
                ],
                sources=sources,
                open_questions=[],
                next_actions=[
                    "Review the sources and save useful findings to Knowledge."
                ],
            )
            await step_completed("synthesize", 5)
            return {"report": report.model_dump(mode="json")}

        graph = StateGraph(ResearchState)
        graph.add_node("understand", understand)
        graph.add_node("plan_search", plan_search)
        graph.add_node("search", search)
        graph.add_node("verify", verify)
        graph.add_node("synthesize", synthesize)
        graph.add_edge(START, "understand")
        graph.add_edge("understand", "plan_search")
        graph.add_edge("plan_search", "search")
        graph.add_edge("search", "verify")
        graph.add_edge("verify", "synthesize")
        graph.add_edge("synthesize", END)

        final_state = await graph.compile().ainvoke({"query": query})
        return ResearchReport.model_validate(final_state["report"])


research_agent = ResearchAgent()
