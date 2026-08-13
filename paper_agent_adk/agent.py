from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from paper_agent.chunker import chunk_document
from paper_agent.loader import PaperLoadError, load_paper


DEFAULT_MODEL = "llama3.1"
DEFAULT_MAX_CHARS = 6000
ALLOWED_DIR_ENV = "PAPER_AGENT_ALLOWED_DIR"


def load_paper_for_analysis(path: str, max_chars: int = DEFAULT_MAX_CHARS) -> dict[str, Any]:
    """Load one PDF, txt, or md paper and return chunked text with source locations."""
    try:
        safe_path = _resolve_allowed_paper_path(path)
        document = chunk_document(load_paper(safe_path), max_chars=max_chars)
    except (PaperLoadError, ValueError) as exc:
        return {
            "ok": False,
            "error": _public_error(exc),
            "path": path,
        }

    if not document.chunks:
        return {
            "ok": False,
            "error": "No readable text chunks were produced.",
            "path": path,
        }

    return {
        "ok": True,
        "title": document.title,
        "source": document.path,
        "chunk_count": len(document.chunks),
        "unreadable_pages": document.unreadable_pages,
        "chunks": [
            {
                "chunk_index": chunk.index,
                "page": chunk.page,
                "text": chunk.text,
            }
            for chunk in document.chunks
        ],
    }


def load_papers_for_comparison(paths: list[str], max_chars: int = DEFAULT_MAX_CHARS) -> dict[str, Any]:
    """Load multiple papers for comparison using the same chunking policy."""
    if len(paths) < 2:
        return {
            "ok": False,
            "error": "Comparison requires at least two paper paths.",
            "papers": [],
        }

    papers = [load_paper_for_analysis(path, max_chars=max_chars) for path in paths]
    errors = [paper.get("error") for paper in papers if not paper.get("ok")]
    return {
        "ok": not errors,
        "error": "; ".join(errors) if errors else None,
        "papers": papers,
    }


def _resolve_allowed_paper_path(path: str) -> Path:
    allowed_root = Path(os.environ.get(ALLOWED_DIR_ENV, ".")).expanduser().resolve(strict=False)
    requested = Path(path).expanduser().resolve(strict=False)
    try:
        requested.relative_to(allowed_root)
    except ValueError as exc:
        raise PaperLoadError(
            f"Paper path is outside the allowed directory. Set {ALLOWED_DIR_ENV} to change it."
        ) from exc
    return requested


def _public_error(exc: Exception) -> str:
    message = str(exc)
    if message.startswith("Paper not found:"):
        return "Paper not found."
    if message.startswith("Paper path is not a file:"):
        return "Paper path is not a file."
    if message.startswith("Failed to read text file as UTF-8:"):
        return "Failed to read text file as UTF-8."
    if message.startswith("Failed to read PDF:"):
        return "Failed to read PDF."
    if message.startswith("No readable text was extracted from:"):
        return "No readable text was extracted."
    return message


def _ollama_model() -> LiteLlm:
    if "OLLAMA_API_BASE" not in os.environ and "OLLAMA_HOST" in os.environ:
        os.environ["OLLAMA_API_BASE"] = os.environ["OLLAMA_HOST"]

    model = os.environ.get("ADK_OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL") or DEFAULT_MODEL
    return LiteLlm(model=f"ollama/{model}")


root_agent = Agent(
    name="paper_reading_comparison_agent",
    model=_ollama_model(),
    description="Reads and compares research papers using a local Ollama model.",
    instruction="""
あなたはローカルLLMで動作する論文読解・比較エージェントです。

必ず次の方針に従ってください。
- ユーザーが指定した論文を主な情報源にする。
- PDF/txt/md のパスが与えられたら、まず load_paper_for_analysis または load_papers_for_comparison を使って本文を読む。
- 論文に書かれている内容と、あなたの解釈を明確に分ける。
- 論文本文にない内容は断定せず、「記載なし」または「判断不能」と書く。
- 根拠は chunk_index と page があれば page を示す。
- 複数論文を比較するときは、研究背景、研究目的、提案手法、実験設定、主な結果、既存手法との違い、研究の限界、今後の発展可能性の同じ観点で整理する。
- 研究内容の正しさ、新規性、再現性、数式の妥当性を最終保証しない。

1本の論文を読む場合は、以下の見出しで回答してください。
1. 研究背景
2. 研究目的
3. 提案手法
4. 実験設定
5. 主な結果
6. 既存手法との違い
7. 研究の限界
8. 今後の発展可能性
9. 根拠
10. 不明点

複数論文を比較する場合は、各論文を同じ観点で整理した後、共通点、相違点、判断不能な点を示してください。
""".strip(),
    tools=[
        load_paper_for_analysis,
        load_papers_for_comparison,
    ],
)
