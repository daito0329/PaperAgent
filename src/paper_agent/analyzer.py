from __future__ import annotations

import json

from pydantic import ValidationError

from .chunker import chunk_document
from .llm import OllamaClient
from .loader import load_paper
from .models import ComparisonReport, PaperDocument, PaperSummary


SUMMARY_FIELDS = [
    "research_background",
    "research_purpose",
    "proposed_method",
    "experimental_setup",
    "main_results",
    "differences_from_existing_methods",
    "limitations",
    "future_work",
]


class AnalysisError(RuntimeError):
    pass


def summarize_paper_path(
    path: str,
    llm: OllamaClient,
    max_chars: int = 6000,
) -> PaperSummary:
    document = chunk_document(load_paper(path), max_chars=max_chars)
    return summarize_document(document, llm=llm)


def summarize_document(document: PaperDocument, llm: OllamaClient) -> PaperSummary:
    if not any(chunk.text.strip() for chunk in document.chunks):
        raise AnalysisError("Cannot summarize a document with no readable text chunks.")

    prompt = _summary_prompt(document)
    raw = llm.generate(prompt)
    data = _parse_json(raw)
    data.setdefault("title", document.title)
    data.setdefault("source", document.path)
    summary = _validate_summary(data)
    _validate_evidence_locations(summary, document)
    return summary


def compare_paper_paths(
    paths: list[str],
    llm: OllamaClient,
    max_chars: int = 6000,
) -> ComparisonReport:
    summaries = [summarize_paper_path(path, llm=llm, max_chars=max_chars) for path in paths]
    return compare_summaries(summaries, llm=llm)


def compare_summaries(summaries: list[PaperSummary], llm: OllamaClient) -> ComparisonReport:
    if len(summaries) < 2:
        raise AnalysisError("Comparison requires at least two papers.")

    prompt = _comparison_prompt(summaries)
    raw = llm.generate(prompt)
    data = _parse_json(raw)
    data["papers"] = [summary.model_dump() for summary in summaries]
    try:
        return ComparisonReport.model_validate(data)
    except ValidationError as exc:
        raise AnalysisError(f"LLM comparison output did not match the expected schema: {exc}") from exc


def _summary_prompt(document: PaperDocument) -> str:
    chunks = "\n\n".join(
        f"[chunk={chunk.index}, page={chunk.page or 'n/a'}]\n{chunk.text}"
        for chunk in document.chunks
    )
    fields = "\n".join(f"- {field}" for field in SUMMARY_FIELDS)
    return f"""
You are a research paper reading assistant. Use only the provided paper text.
Separate what the paper states from interpretation. Do not invent missing facts.

Return strict JSON with these keys:
- title
- source
{fields}
- evidence: array of objects with aspect, source, chunk_index, page, text
- unknowns: array of strings

For unknown information, write "記載なし" or add it to unknowns.
Keep evidence text short and grounded in the supplied chunks.

Paper title: {document.title}
Paper source: {document.path}

Paper text:
{chunks}
""".strip()


def _comparison_prompt(summaries: list[PaperSummary]) -> str:
    payload = [summary.model_dump() for summary in summaries]
    return f"""
You are comparing research paper summaries.
Use the same comparison criteria for every paper.
Return strict JSON with these keys:
- common_points: array of strings
- differences: array of strings
- unknowns: array of strings

Do not add new claims that are absent from the summaries.

Summaries:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def _parse_json(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"LLM output was not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AnalysisError("LLM output must be a JSON object.")
    return data


def _validate_summary(data: dict) -> PaperSummary:
    for field in SUMMARY_FIELDS:
        data.setdefault(field, "記載なし")
    data.setdefault("evidence", [])
    data.setdefault("unknowns", [])
    try:
        return PaperSummary.model_validate(data)
    except ValidationError as exc:
        raise AnalysisError(f"LLM summary output did not match the expected schema: {exc}") from exc


def _validate_evidence_locations(summary: PaperSummary, document: PaperDocument) -> None:
    chunks_by_index = {chunk.index: chunk for chunk in document.chunks}
    for evidence in summary.evidence:
        chunk = chunks_by_index.get(evidence.chunk_index)
        if chunk is None:
            raise AnalysisError(
                f"LLM evidence references missing chunk_index: {evidence.chunk_index}"
            )
        if evidence.page is not None and chunk.page != evidence.page:
            raise AnalysisError(
                "LLM evidence page does not match the referenced chunk: "
                f"chunk_index={evidence.chunk_index}, page={evidence.page}"
            )
