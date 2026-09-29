from app.agents.research.schemas import ResearchReport, ResearchSourceData


def test_research_report_schema() -> None:
    report = ResearchReport(
        title="Example",
        summary="Summary",
        key_findings=["Finding"],
        sources=[
            ResearchSourceData(
                url="https://example.com/source",
                title="Source",
                snippet="Evidence",
            )
        ],
    )

    payload = report.model_dump(mode="json")
    assert payload["sources"][0]["url"].startswith("https://")
    assert report.sources[0].title == "Source"
