from paper_agent_adk.agent import load_paper_for_analysis, load_papers_for_comparison, root_agent


def test_adk_root_agent_is_configured():
    assert root_agent.name == "paper_reading_comparison_agent"
    assert len(root_agent.tools) == 2


def test_load_paper_for_analysis_returns_error_for_missing_file():
    result = load_paper_for_analysis("missing.txt")

    assert result["ok"] is False
    assert "Paper not found" in result["error"]


def test_load_papers_for_comparison_requires_two_paths():
    result = load_papers_for_comparison(["one.txt"])

    assert result["ok"] is False
    assert "at least two" in result["error"]


def test_load_papers_for_comparison_reports_partial_failures(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPER_AGENT_ALLOWED_DIR", str(tmp_path))
    paper = tmp_path / "paper.txt"
    paper.write_text("本文", encoding="utf-8")

    result = load_papers_for_comparison([str(paper), str(tmp_path / "missing.txt")])

    assert result["ok"] is False
    assert "Paper not found" in result["error"]
    assert result["papers"][0]["ok"] is True
    assert result["papers"][1]["ok"] is False


def test_load_paper_for_analysis_allows_file_inside_allowed_dir(monkeypatch, tmp_path):
    paper = tmp_path / "paper.txt"
    paper.write_text("本文", encoding="utf-8")
    monkeypatch.setenv("PAPER_AGENT_ALLOWED_DIR", str(tmp_path))

    result = load_paper_for_analysis(str(paper))

    assert result["ok"] is True
    assert result["title"] == "paper"
    assert result["chunk_count"] == 1
    assert result["chunks"][0]["text"] == "本文"


def test_load_paper_for_analysis_rejects_paths_outside_allowed_dir(monkeypatch, tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    paper = outside / "paper.txt"
    paper.write_text("secret", encoding="utf-8")
    monkeypatch.setenv("PAPER_AGENT_ALLOWED_DIR", str(allowed))

    result = load_paper_for_analysis(str(paper))

    assert result["ok"] is False
    assert "outside the allowed directory" in result["error"]


def test_load_paper_for_analysis_allows_symlink_inside_allowed_dir(monkeypatch, tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("本文", encoding="utf-8")
    link = tmp_path / "paper.txt"
    link.symlink_to(target)
    monkeypatch.setenv("PAPER_AGENT_ALLOWED_DIR", str(tmp_path))

    result = load_paper_for_analysis(str(link))

    assert result["ok"] is True
    assert result["chunks"][0]["text"] == "本文"


def test_load_paper_for_analysis_rejects_symlink_escape(monkeypatch, tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    target = outside / "secret.txt"
    target.write_text("secret", encoding="utf-8")
    link = allowed / "paper.txt"
    link.symlink_to(target)
    monkeypatch.setenv("PAPER_AGENT_ALLOWED_DIR", str(allowed))

    result = load_paper_for_analysis(str(link))

    assert result["ok"] is False
    assert "outside the allowed directory" in result["error"]
