from paper_agent.chunker import chunk_document
from paper_agent.models import DocumentChunk, PaperDocument


def test_chunk_document_preserves_order_and_page():
    document = PaperDocument(
        path="paper.txt",
        title="paper",
        chunks=[
            DocumentChunk(source="paper.txt", index=0, page=3, text="a" * 700 + "\n\n" + "b" * 700),
        ],
    )

    chunked = chunk_document(document, max_chars=1000)

    assert [chunk.index for chunk in chunked.chunks] == [0, 1]
    assert [chunk.page for chunk in chunked.chunks] == [3, 3]
    assert chunked.chunks[0].text == "a" * 700
    assert chunked.chunks[1].text == "b" * 700


def test_chunk_document_rejects_tiny_chunks():
    document = PaperDocument(path="paper.txt", title="paper", chunks=[])

    try:
        chunk_document(document, max_chars=100)
    except ValueError as exc:
        assert "max_chars" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
