from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.research.schemas import ResearchReport
from app.db.models import EvaluationResult


async def evaluate_research(
    session: AsyncSession,
    run_id: UUID,
    report: ResearchReport,
) -> list[EvaluationResult]:
    checks = [
        ("report_schema_valid", True, {"schema": "ResearchReport"}),
        ("title_present", bool(report.title.strip()), {}),
        ("summary_present", bool(report.summary.strip()), {}),
        (
            "source_present",
            bool(report.sources),
            {"source_count": len(report.sources)},
        ),
    ]
    rows: list[EvaluationResult] = []
    for metric_name, passed, evidence in checks:
        row = EvaluationResult(
            run_id=run_id,
            evaluation_type="DETERMINISTIC",
            metric_name=metric_name,
            evaluator_key="research-deterministic",
            evaluator_version="0.1",
            status="PASS" if passed else "FAIL",
            evidence_json=evidence,
        )
        session.add(row)
        rows.append(row)
    await session.commit()
    return rows
