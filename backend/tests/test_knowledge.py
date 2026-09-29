from uuid import uuid4

from app.api.routes.knowledge import render_knowledge_markdown
from app.db.models import ResearchItem


def test_render_knowledge_markdown_includes_findings_and_sources() -> None:
    research = ResearchItem(
        id=uuid4(),
        title="Framework comparison",
        query="Compare A and B",
        summary="Short summary",
        status="COMPLETED",
        structured_result_json={
            "summary": "Structured summary",
            "key_findings": ["Finding one"],
            "sources": [
                {
                    "title": "Official docs",
                    "url": "https://example.com/docs",
                }
            ],
            "next_actions": ["Build a small benchmark."],
        },
    )

    content = render_knowledge_markdown(research)

    assert "# Framework comparison" in content
    assert "Finding one" in content
    assert "[Official docs](https://example.com/docs)" in content
    assert "Build a small benchmark." in content
