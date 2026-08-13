from __future__ import annotations

import html
import json
import re

from .models import ComparisonReport, PaperSummary


ASPECT_LABELS = {
    "research_background": "研究背景",
    "research_purpose": "研究目的",
    "proposed_method": "提案手法",
    "experimental_setup": "実験設定",
    "main_results": "主な結果",
    "differences_from_existing_methods": "既存手法との違い",
    "limitations": "研究の限界",
    "future_work": "今後の発展可能性",
}


def render_summary(summary: PaperSummary, output_format: str = "markdown") -> str:
    if output_format == "json":
        return summary.model_dump_json(indent=2)
    if output_format != "markdown":
        raise ValueError(f"Unsupported output format: {output_format}")

    lines = [
        f"# {_markdown_text(summary.title)}",
        "",
        f"Source: {_markdown_text(summary.source)}",
        "",
    ]
    for field, label in ASPECT_LABELS.items():
        lines.extend([f"## {label}", _markdown_text(getattr(summary, field)), ""])

    if summary.evidence:
        lines.extend(["## 根拠", ""])
        for evidence in summary.evidence:
            location = f"page {evidence.page}" if evidence.page else f"chunk {evidence.chunk_index}"
            lines.append(
                f"- {ASPECT_LABELS[evidence.aspect]} ({location}): {_markdown_text(evidence.text)}"
            )
        lines.append("")

    if summary.unknowns:
        lines.extend(["## 不明点", ""])
        lines.extend(f"- {_markdown_text(unknown)}" for unknown in summary.unknowns)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_comparison(report: ComparisonReport, output_format: str = "markdown") -> str:
    if output_format == "json":
        return report.model_dump_json(indent=2)
    if output_format != "markdown":
        raise ValueError(f"Unsupported output format: {output_format}")

    lines = ["# 論文比較", ""]
    for summary in report.papers:
        lines.extend(
            [
                f"## {_markdown_text(summary.title)}",
                f"- Source: {_markdown_text(summary.source)}",
            ]
        )
        for field, label in ASPECT_LABELS.items():
            lines.append(f"- {label}: {_markdown_text(getattr(summary, field))}")
        lines.append("")

    lines.extend(["## 共通点", ""])
    lines.extend(f"- {_markdown_text(point)}" for point in report.common_points or ["記載なし"])
    lines.extend(["", "## 相違点", ""])
    lines.extend(f"- {_markdown_text(difference)}" for difference in report.differences or ["記載なし"])

    if report.unknowns:
        lines.extend(["", "## 不明点", ""])
        lines.extend(f"- {_markdown_text(unknown)}" for unknown in report.unknowns)

    return "\n".join(lines).strip() + "\n"


def dump_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _markdown_text(value: object) -> str:
    text = html.escape(str(value), quote=False)
    text = re.sub(r"[\r\n]+", " ", text)
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>])", r"\\\1", text)
