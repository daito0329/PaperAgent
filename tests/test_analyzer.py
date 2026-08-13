import json

from paper_agent.analyzer import AnalysisError, compare_summaries, summarize_document
from paper_agent.models import DocumentChunk, PaperDocument, PaperSummary


class FakeLLM:
    def __init__(self, response: dict):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.response, ensure_ascii=False)


def test_summarize_document_defaults_missing_fields():
    document = PaperDocument(
        path="paper.txt",
        title="paper",
        chunks=[DocumentChunk(source="paper.txt", index=0, text="本文", page=None)],
    )
    llm = FakeLLM({"research_background": "背景"})

    summary = summarize_document(document, llm=llm)

    assert summary.title == "paper"
    assert summary.source == "paper.txt"
    assert summary.research_background == "背景"
    assert summary.research_purpose == "記載なし"
    assert "本文" in llm.prompts[0]


def test_compare_summaries_keeps_original_papers():
    summaries = [
        _summary("paper1", "method A"),
        _summary("paper2", "method B"),
    ]
    llm = FakeLLM({"common_points": ["同じ課題"], "differences": ["手法が異なる"], "unknowns": []})

    report = compare_summaries(summaries, llm=llm)

    assert [paper.title for paper in report.papers] == ["paper1", "paper2"]
    assert report.common_points == ["同じ課題"]
    assert report.differences == ["手法が異なる"]


def test_summarize_document_rejects_empty_chunk_list():
    document = PaperDocument(path="paper.txt", title="paper", chunks=[])
    llm = FakeLLM({"research_background": "背景"})

    try:
        summarize_document(document, llm=llm)
    except AnalysisError as exc:
        assert "no readable text chunks" in str(exc)
    else:
        raise AssertionError("Expected AnalysisError")


def test_summarize_document_rejects_missing_evidence_chunk():
    document = PaperDocument(
        path="paper.txt",
        title="paper",
        chunks=[DocumentChunk(source="paper.txt", index=0, text="本文", page=None)],
    )
    llm = FakeLLM(
        {
            "research_background": "背景",
            "evidence": [
                {
                    "aspect": "research_background",
                    "source": "paper.txt",
                    "chunk_index": 99,
                    "page": None,
                    "text": "根拠",
                }
            ],
        }
    )

    try:
        summarize_document(document, llm=llm)
    except AnalysisError as exc:
        assert "missing chunk_index" in str(exc)
    else:
        raise AssertionError("Expected AnalysisError")


def test_summarize_document_rejects_mismatched_evidence_page():
    document = PaperDocument(
        path="paper.pdf",
        title="paper",
        chunks=[DocumentChunk(source="paper.pdf", index=0, text="本文", page=1)],
    )
    llm = FakeLLM(
        {
            "research_background": "背景",
            "evidence": [
                {
                    "aspect": "research_background",
                    "source": "paper.pdf",
                    "chunk_index": 0,
                    "page": 2,
                    "text": "根拠",
                }
            ],
        }
    )

    try:
        summarize_document(document, llm=llm)
    except AnalysisError as exc:
        assert "page does not match" in str(exc)
    else:
        raise AssertionError("Expected AnalysisError")


def _summary(title: str, method: str) -> PaperSummary:
    return PaperSummary(
        title=title,
        source=f"{title}.txt",
        research_background="背景",
        research_purpose="目的",
        proposed_method=method,
        experimental_setup="実験",
        main_results="結果",
        differences_from_existing_methods="差分",
        limitations="限界",
        future_work="発展",
    )
