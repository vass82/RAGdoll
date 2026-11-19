"""Unit tests for indexing document chunks into a vector store."""

from typing import Any

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.embeddings.fake import DeterministicFakeEmbedding

from app.infrastructure.vector_store import create_in_memory_vector_store
from app.rag.indexing import IndexingError, index_documents

CHUNKS = [
    Document(
        page_content="RAGdoll uses FastAPI for its HTTP API.",
        metadata={"source": "overview.md", "relative_path": "overview.md"},
    ),
    Document(
        page_content="Solver output is written to .pos files.",
        metadata={"source": "usage.md", "relative_path": "guides/usage.md"},
    ),
]


class FailingEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Embedding model unavailable.")

    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("Embedding model unavailable.")


class RejectingStore:
    """Vector store stand-in whose insertion always fails."""

    def add_documents(self, documents: list[Document]) -> None:
        raise RuntimeError("Insertion failed.")


class RecordingStore:
    """Vector store stand-in that records every insertion."""

    def __init__(self) -> None:
        self.calls: list[list[Document]] = []

    def add_documents(self, documents: list[Document]) -> None:
        self.calls.append(documents)


def test_indexing_returns_number_of_chunks_and_makes_them_searchable() -> None:
    store = create_in_memory_vector_store(DeterministicFakeEmbedding(size=32))

    count = index_documents(store, CHUNKS)

    assert count == 2
    results = store.as_retriever(search_kwargs={"k": 2}).invoke(
        "Solver output is written to .pos files."
    )
    assert {doc.page_content: doc.metadata for doc in results} == {
        chunk.page_content: chunk.metadata for chunk in CHUNKS
    }


def test_empty_input_indexes_nothing_and_does_not_touch_the_store() -> None:
    store = RecordingStore()

    count = index_documents(store, [])

    assert count == 0
    assert store.calls == []


def test_embedding_failure_raises_indexing_error() -> None:
    store = create_in_memory_vector_store(FailingEmbeddings())

    with pytest.raises(IndexingError, match="Failed to index") as exc_info:
        index_documents(store, CHUNKS)

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_vector_store_insertion_failure_raises_indexing_error() -> None:
    with pytest.raises(IndexingError) as exc_info:
        index_documents(RejectingStore(), CHUNKS)  # type: ignore[arg-type]

    assert str(exc_info.value.__cause__) == "Insertion failed."


def test_all_chunks_are_passed_to_the_store_in_one_call() -> None:
    store = RecordingStore()

    index_documents(store, tuple(CHUNKS))  # type: ignore[arg-type]

    assert store.calls == [CHUNKS]
    assert all(isinstance(chunk, Document) for chunk in store.calls[0])
    assert [chunk.metadata for chunk in store.calls[0]] == [
        chunk.metadata for chunk in CHUNKS
    ]


def test_store_receives_no_extra_keys_in_metadata() -> None:
    store: Any = RecordingStore()

    index_documents(store, CHUNKS)

    assert set(store.calls[0][0].metadata) == {"source", "relative_path"}
