from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SummaryAspect = Literal[
    "research_background",
    "research_purpose",
    "proposed_method",
    "experimental_setup",
    "main_results",
    "differences_from_existing_methods",
    "limitations",
    "future_work",
]


class DocumentChunk(BaseModel):
    source: str
    index: int
    text: str
    page: int | None = None


class PaperDocument(BaseModel):
    path: str
    title: str
    chunks: list[DocumentChunk]
    unreadable_pages: list[int] = Field(default_factory=list)


class Evidence(BaseModel):
    aspect: SummaryAspect
    source: str
    chunk_index: int
    page: int | None = None
    text: str = Field(description="Short supporting text from the paper.")


class PaperSummary(BaseModel):
    title: str
    source: str
    research_background: str
    research_purpose: str
    proposed_method: str
    experimental_setup: str
    main_results: str
    differences_from_existing_methods: str
    limitations: str
    future_work: str
    evidence: list[Evidence] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class ComparisonReport(BaseModel):
    papers: list[PaperSummary]
    common_points: list[str]
    differences: list[str]
    unknowns: list[str] = Field(default_factory=list)
