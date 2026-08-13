from __future__ import annotations

from pathlib import Path

from .models import DocumentChunk, PaperDocument


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}


class PaperLoadError(ValueError):
    pass


def load_paper(path: str | Path) -> PaperDocument:
    paper_path = Path(path).expanduser()
    if not paper_path.exists():
        raise PaperLoadError(f"Paper not found: {paper_path}")
    if not paper_path.is_file():
        raise PaperLoadError(f"Paper path is not a file: {paper_path}")

    suffix = paper_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise PaperLoadError(f"Unsupported file type '{suffix}'. Supported: {supported}")

    if suffix == ".pdf":
        chunks, unreadable_pages = _load_pdf(paper_path)
    else:
        chunks = _load_text(paper_path)
        unreadable_pages = []

    if not any(chunk.text.strip() for chunk in chunks):
        raise PaperLoadError(f"No readable text was extracted from: {paper_path}")

    return PaperDocument(
        path=str(paper_path),
        title=paper_path.stem,
        chunks=chunks,
        unreadable_pages=unreadable_pages,
    )


def _load_text(path: Path) -> list[DocumentChunk]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PaperLoadError(f"Failed to read text file as UTF-8: {path}") from exc
    return [DocumentChunk(source=str(path), index=0, text=text, page=None)]


def _load_pdf(path: Path) -> tuple[list[DocumentChunk], list[int]]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise PaperLoadError("PDF support requires the 'pypdf' package.") from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PaperLoadError(f"Failed to read PDF: {path}") from exc

    chunks: list[DocumentChunk] = []
    unreadable_pages: list[int] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
            unreadable_pages.append(page_index)
        chunks.append(
            DocumentChunk(
                source=str(path),
                index=page_index - 1,
                text=text,
                page=page_index,
            )
        )
    return chunks, unreadable_pages
