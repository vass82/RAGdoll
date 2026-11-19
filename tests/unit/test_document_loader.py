"""Unit tests for loading Markdown documents from the filesystem."""

from pathlib import Path

import pytest

from app.infrastructure.document_loader import (
    DocumentLoadError,
    load_markdown_documents,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_single_markdown_document_is_loaded_with_metadata(tmp_path: Path) -> None:
    _write(tmp_path / "overview.md", "# Overview\n\nRAGdoll is a RAG backend.\n")

    documents = load_markdown_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].page_content == "# Overview\n\nRAGdoll is a RAG backend.\n"
    assert documents[0].metadata == {
        "source": "overview.md",
        "relative_path": "overview.md",
    }


def test_nested_directories_are_loaded_in_sorted_order(tmp_path: Path) -> None:
    _write(tmp_path / "zeta.md", "Zeta")
    _write(tmp_path / "guides" / "install.md", "Install")
    _write(tmp_path / "guides" / "deep" / "usage.md", "Usage")

    documents = load_markdown_documents(tmp_path)

    assert [doc.page_content for doc in documents] == ["Usage", "Install", "Zeta"]
    assert [doc.metadata["relative_path"] for doc in documents] == [
        "guides/deep/usage.md",
        "guides/install.md",
        "zeta.md",
    ]
    assert [doc.metadata["source"] for doc in documents] == [
        "usage.md",
        "install.md",
        "zeta.md",
    ]


def test_non_markdown_files_are_ignored(tmp_path: Path) -> None:
    _write(tmp_path / "notes.md", "Keep me")
    _write(tmp_path / "data.txt", "ignore me")
    _write(tmp_path / "diagram.png", "not really a png")
    _write(tmp_path / "config.json", "{}")

    documents = load_markdown_documents(tmp_path)

    assert [doc.metadata["source"] for doc in documents] == ["notes.md"]


def test_empty_and_whitespace_only_markdown_files_are_skipped(tmp_path: Path) -> None:
    _write(tmp_path / "empty.md", "")
    _write(tmp_path / "blank.md", "  \n\t\n")
    _write(tmp_path / "content.md", "Real content")

    documents = load_markdown_documents(tmp_path)

    assert [doc.metadata["source"] for doc in documents] == ["content.md"]


def test_empty_directory_returns_no_documents(tmp_path: Path) -> None:
    assert load_markdown_documents(tmp_path) == []


def test_missing_directory_raises_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError, match="does-not-exist"):
        load_markdown_documents(missing)


def test_file_path_instead_of_directory_raises(tmp_path: Path) -> None:
    file_path = _write(tmp_path / "overview.md", "Content")

    with pytest.raises(NotADirectoryError, match="overview.md"):
        load_markdown_documents(file_path)


def test_non_utf8_markdown_raises_document_load_error(tmp_path: Path) -> None:
    (tmp_path / "broken.md").write_bytes(b"\xff\xfe\x00invalid")

    with pytest.raises(DocumentLoadError, match="broken.md") as exc_info:
        load_markdown_documents(tmp_path)

    assert isinstance(exc_info.value.__cause__, UnicodeDecodeError)
