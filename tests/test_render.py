from paper_agent.models import ComparisonReport, Evidence, PaperSummary
from paper_agent.render import render_comparison, render_summary


def test_render_summary_markdown_contains_evidence():
    summary = _summary(
        evidence=[
            Evidence(
                aspect="research_background",
                source="paper.txt",
                chunk_index=0,
                page=None,
                text="根拠文",
            )
        ]
    )

    output = render_summary(summary)

    assert "# paper" in output
    assert "## 研究背景" in output
    assert "根拠文" in output


def test_render_comparison_json():
    report = ComparisonReport(
        papers=[_summary()],
        common_points=["共通"],
        differences=["相違"],
    )

    output = render_comparison(report, output_format="json")

    assert '"common_points"' in output
    assert "共通" in output


def test_render_summary_escapes_untrusted_markdown_html():
    summary = _summary(
        evidence=[
            Evidence(
                aspect="research_background",
                source="paper.txt",
                chunk_index=0,
                page=None,
                text="[x](javascript:alert(1)) <script>alert(1)</script>",
            )
        ]
    )
    summary.title = "<script>alert(1)</script>"
    summary.research_background = "[x](javascript:alert(1))"
    summary.unknowns = ["<img src=x onerror=alert(1)>"]

    output = render_summary(summary)

    assert "<script>" not in output
    assert "<img" not in output
    assert "\\[x\\]\\(javascript:alert\\(1\\)\\)" in output
    assert "&lt;script&gt;" in output


def test_render_comparison_escapes_untrusted_markdown_html():
    summary = _summary()
    summary.title = "<script>alert(1)</script>"
    report = ComparisonReport(
        papers=[summary],
        common_points=["[x](javascript:alert(1))"],
        differences=["<img src=x onerror=alert(1)>"],
        unknowns=["**not bold**"],
    )

    output = render_comparison(report)

    assert "<script>" not in output
    assert "<img" not in output
    assert "\\[x\\]\\(javascript:alert\\(1\\)\\)" in output
    assert "\\*\\*not bold\\*\\*" in output


def _summary(evidence=None) -> PaperSummary:
    return PaperSummary(
        title="paper",
        source="paper.txt",
        research_background="背景",
        research_purpose="目的",
        proposed_method="手法",
        experimental_setup="実験",
        main_results="結果",
        differences_from_existing_methods="差分",
        limitations="限界",
        future_work="発展",
        evidence=evidence or [],
    )
