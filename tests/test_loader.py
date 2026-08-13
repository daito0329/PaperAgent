from pathlib import Path
import sys
import types

from paper_agent.loader import PaperLoadError, load_paper


def test_load_text_file(tmp_path: Path):
    paper = tmp_path / "paper.txt"
    paper.write_text("研究背景\n本文", encoding="utf-8")

    document = load_paper(paper)

    assert document.title == "paper"
    assert len(document.chunks) == 1
    assert document.chunks[0].text == "研究背景\n本文"


def test_load_empty_text_file_fails(tmp_path: Path):
    paper = tmp_path / "empty.txt"
    paper.write_text("", encoding="utf-8")

    try:
        load_paper(paper)
    except PaperLoadError as exc:
        assert "No readable text" in str(exc)
    else:
        raise AssertionError("Expected PaperLoadError")


def test_load_unsupported_file_fails(tmp_path: Path):
    paper = tmp_path / "paper.docx"
    paper.write_text("content", encoding="utf-8")

    try:
        load_paper(paper)
    except PaperLoadError as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("Expected PaperLoadError")


def test_load_non_utf8_text_file_fails_with_load_error(tmp_path: Path):
    paper = tmp_path / "paper.txt"
    paper.write_bytes("本文".encode("cp932"))

    try:
        load_paper(paper)
    except PaperLoadError as exc:
        assert "UTF-8" in str(exc)
    else:
        raise AssertionError("Expected PaperLoadError")


def test_load_pdf_records_unreadable_pages(monkeypatch, tmp_path: Path):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF fake")

    class FakePage:
        def __init__(self, text=None, error=False):
            self.text = text
            self.error = error

        def extract_text(self):
            if self.error:
                raise RuntimeError("cannot extract")
            return self.text

    class FakeReader:
        def __init__(self, path: str):
            self.pages = [
                FakePage("first page"),
                FakePage(error=True),
                FakePage("third page"),
            ]

    monkeypatch.setitem(sys.modules, "pypdf", types.SimpleNamespace(PdfReader=FakeReader))

    document = load_paper(paper)

    assert [chunk.text for chunk in document.chunks] == ["first page", "", "third page"]
    assert document.unreadable_pages == [2]
