"""Splitting of loaded documents into smaller chunks for indexing."""

from collections.abc import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    documents: Iterable[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Split documents into chunks using ``RecursiveCharacterTextSplitter``.

    Every chunk keeps a copy of its parent document's metadata.

    :param documents: Documents to split. May be empty.
    :type documents: Iterable[Document]
    :param chunk_size: Maximum number of characters per chunk.
    :type chunk_size: int
    :param chunk_overlap: Number of characters shared by adjacent chunks.
        Must be smaller than ``chunk_size``.
    :type chunk_overlap: int
    :returns: The chunks, in the order their source documents were supplied.
    :rtype: list[Document]
    :raises ValueError: If ``chunk_size`` is not positive, or ``chunk_overlap``
        is negative or not smaller than ``chunk_size``.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(list(documents))
