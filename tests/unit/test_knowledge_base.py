"""Unit tests for building the indexed knowledge base from Markdown files."""

from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.embeddings.fake import DeterministicFakeEmbedding

from app.core.config import Settings
from app.rag.indexing import IndexingError
from app.services.knowledge_base import KnowledgeBaseError, build_knowledge_base


class FailingEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Embedding model unavailable.")

    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("Embedding model unavailable.")


def _settings(documents_dir: Path, **overrides: int) -> Settings:
    return Settings(_env_file=None, documents_dir=documents_dir, **overrides)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_chunks(store) -> list:  # type: ignore[no-untyped-def]
    return store.as_retriever(search_kwargs={"k": 100}).invoke("anything")


def test_all_nested_documents_are_indexed_with_metadata(tmp_path: Path) -> None:
    _write(tmp_path / "overview.md", "RAGdoll uses FastAPI.")
    _write(tmp_path / "guides" / "install.md", "Install with uv sync.")

    store = build_knowledge_base(
        _settings(tmp_path, chunk_size=1000, chunk_overlap=0),
        DeterministicFakeEmbedding(size=32),
    )

    chunks = _all_chunks(store)
    assert {chunk.page_content: chunk.metadata for chunk in chunks} == {
        "RAGdoll uses FastAPI.": {
            "source": "overview.md",
            "relative_path": "overview.md",
        },
        "Install with uv sync.": {
            "source": "install.md",
            "relative_path": "guides/install.md",
        },
    }


def test_long_documents_are_indexed_as_bounded_chunks(tmp_path: Path) -> None:
    _write(tmp_path / "long.md", " ".join(f"word{i}" for i in range(300)))

    store = build_knowledge_base(
        _settings(tmp_path, chunk_size=120, chunk_overlap=20),
        DeterministicFakeEmbedding(size=32),
    )

    chunks = _all_chunks(store)
    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 120 for chunk in chunks)
    assert all(chunk.metadata["source"] == "long.md" for chunk in chunks)


def test_empty_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeBaseError, match="No Markdown documents"):
        build_knowledge_base(_settings(tmp_path), DeterministicFakeEmbedding(size=8))


def test_missing_directory_is_rejected_with_cause(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(KnowledgeBaseError, match="Could not load") as exc_info:
        build_knowledge_base(_settings(missing), DeterministicFakeEmbedding(size=8))

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


def test_invalid_chunk_overlap_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path / "overview.md", "RAGdoll uses FastAPI.")

    with pytest.raises(KnowledgeBaseError, match="chunk size or chunk overlap"):
        build_knowledge_base(
            _settings(tmp_path, chunk_size=100, chunk_overlap=100),
            DeterministicFakeEmbedding(size=8),
        )


def test_embedding_failure_is_reported_and_no_store_is_returned(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "overview.md", "RAGdoll uses FastAPI.")

    with pytest.raises(KnowledgeBaseError, match="Failed to index") as exc_info:
        build_knowledge_base(_settings(tmp_path), FailingEmbeddings())

    assert isinstance(exc_info.value.__cause__, IndexingError)
