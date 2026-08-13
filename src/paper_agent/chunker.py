from __future__ import annotations

from .models import DocumentChunk, PaperDocument


def chunk_document(document: PaperDocument, max_chars: int = 6000) -> PaperDocument:
    if max_chars <= 500:
        raise ValueError("max_chars must be greater than 500")

    chunks: list[DocumentChunk] = []
    next_index = 0
    for source_chunk in document.chunks:
        text = source_chunk.text.strip()
        if not text:
            continue
        for part in _split_text(text, max_chars=max_chars):
            chunks.append(
                DocumentChunk(
                    source=source_chunk.source,
                    index=next_index,
                    text=part,
                    page=source_chunk.page,
                )
            )
            next_index += 1

    return PaperDocument(
        path=document.path,
        title=document.title,
        chunks=chunks,
        unreadable_pages=document.unreadable_pages,
    )


def _split_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        return [text[:max_chars]]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_text(paragraph, max_chars=max_chars))
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)
    return chunks


def _split_long_text(text: str, max_chars: int) -> list[str]:
    return [text[index : index + max_chars].strip() for index in range(0, len(text), max_chars)]
