"""Unit tests for splitting loaded documents into chunks."""

import itertools

import pytest
from langchain_core.documents import Document

from app.rag.chunking import split_documents


def _long_text(words: int) -> str:
    return " ".join(f"word{i}" for i in range(words))


def test_chunks_respect_configured_chunk_size() -> None:
    document = Document(page_content=_long_text(200), metadata={"source": "a.md"})

    chunks = split_documents([document], chunk_size=100, chunk_overlap=0)

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)


def test_unbreakable_text_is_still_split_within_chunk_size() -> None:
    document = Document(page_content="x" * 250, metadata={"source": "a.md"})

    chunks = split_documents([document], chunk_size=100, chunk_overlap=0)

    assert [len(chunk.page_content) for chunk in chunks] == [100, 100, 50]


def test_adjacent_chunks_overlap_when_overlap_is_configured() -> None:
    document = Document(page_content=_long_text(200), metadata={"source": "a.md"})

    chunks = split_documents([document], chunk_size=100, chunk_overlap=30)

    for previous, current in itertools.pairwise(chunks):
        shared_tail = previous.page_content[-30:].split()[-1]
        assert shared_tail in current.page_content.split()


def test_short_document_yields_a_single_chunk_with_original_content() -> None:
    document = Document(page_content="Short text.", metadata={"source": "a.md"})

    chunks = split_documents([document], chunk_size=100, chunk_overlap=10)

    assert [chunk.page_content for chunk in chunks] == ["Short text."]


def test_metadata_is_copied_to_every_chunk() -> None:
    metadata = {"source": "guides/install.md", "relative_path": "guides/install.md"}
    document = Document(page_content=_long_text(200), metadata=metadata)

    chunks = split_documents([document], chunk_size=100, chunk_overlap=10)

    assert len(chunks) > 1
    assert all(chunk.metadata == metadata for chunk in chunks)


def test_each_document_keeps_its_own_metadata_across_chunks() -> None:
    first = Document(page_content=_long_text(100), metadata={"source": "a.md"})
    second = Document(page_content=_long_text(100), metadata={"source": "b.md"})

    chunks = split_documents([first, second], chunk_size=80, chunk_overlap=0)

    sources = [chunk.metadata["source"] for chunk in chunks]
    assert sources == sorted(sources)
    assert set(sources) == {"a.md", "b.md"}


def test_splitting_does_not_mutate_input_metadata() -> None:
    metadata = {"source": "a.md"}
    document = Document(page_content=_long_text(200), metadata=metadata)

    chunks = split_documents([document], chunk_size=100, chunk_overlap=0)
    chunks[0].metadata["source"] = "changed.md"

    assert metadata == {"source": "a.md"}
    assert document.metadata == {"source": "a.md"}


def test_empty_input_returns_no_chunks() -> None:
    assert split_documents([], chunk_size=100, chunk_overlap=10) == []


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_non_positive_chunk_size_is_rejected(chunk_size: int) -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        split_documents([], chunk_size=chunk_size, chunk_overlap=0)


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"), [(100, -1), (100, 100), (100, 150)]
)
def test_invalid_overlap_is_rejected(chunk_size: int, chunk_overlap: int) -> None:
    with pytest.raises(ValueError, match="chunk_overlap"):
        split_documents([], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
