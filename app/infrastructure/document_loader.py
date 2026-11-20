"""Filesystem loader for Markdown source documents.

Documents are discovered recursively under a root directory. Only files with a
``.md`` suffix are loaded; other files are ignored, and empty or
whitespace-only Markdown files produce no document.
"""

from pathlib import Path

from langchain_core.documents import Document

MARKDOWN_SUFFIX = ".md"


class DocumentLoadError(RuntimeError):
    """Raised when a Markdown file cannot be read as UTF-8 text."""


def load_markdown_documents(directory: Path) -> list[Document]:
    """Recursively load Markdown files from a directory as LangChain documents.

    Files are returned in sorted path order so results are deterministic.
    Each document's metadata contains:

    * ``source``: the file name (for example ``overview.md``).
    * ``relative_path``: the path relative to ``directory`` using forward
      slashes (for example ``guides/install.md``).

    :param directory: Root directory to search for Markdown files.
    :type directory: Path
    :returns: One document per non-empty Markdown file. May be empty.
    :rtype: list[Document]
    :raises FileNotFoundError: If ``directory`` does not exist.
    :raises NotADirectoryError: If ``directory`` is not a directory.
    :raises DocumentLoadError: If a Markdown file is not valid UTF-8.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Documents directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Documents path is not a directory: {root}")

    documents: list[Document] = []
    for path in sorted(root.rglob(f"*{MARKDOWN_SUFFIX}")):
        if not path.is_file():
            continue
        content = _read_markdown(path)
        if not content.strip():
            continue
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": path.name,
                    "relative_path": path.relative_to(root).as_posix(),
                },
            )
        )
    return documents


def _read_markdown(path: Path) -> str:
    """Read a Markdown file as UTF-8 text.

    :param path: The file to read.
    :type path: Path
    :returns: The file contents.
    :rtype: str
    :raises DocumentLoadError: If the file is not valid UTF-8.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError(f"Markdown file is not valid UTF-8: {path}") from exc
