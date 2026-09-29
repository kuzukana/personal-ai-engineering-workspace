from pydantic import BaseModel, Field, HttpUrl


class ResearchSourceData(BaseModel):
    url: HttpUrl
    title: str
    snippet: str | None = None
    source_type: str = "OTHER"
    verification_status: str = "UNVERIFIED"


class ResearchReport(BaseModel):
    title: str
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    sources: list[ResearchSourceData] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
