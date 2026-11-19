"""Construction of the populated in-memory knowledge base.

The knowledge base is built once from the Markdown documents in the configured
directory: load, split into chunks, embed, and index. Any failure raises
:class:`KnowledgeBaseError` so that no partially populated store is returned.
"""

import logging

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

from app.core.config import Settings
from app.infrastructure.document_loader import (
    DocumentLoadError,
    load_markdown_documents,
)
from app.infrastructure.vector_store import create_in_memory_vector_store
from app.rag.chunking import split_documents
from app.rag.indexing import IndexingError, index_documents

logger = logging.getLogger(__name__)


class KnowledgeBaseError(RuntimeError):
    """Raised when the knowledge base cannot be built from the documents."""


def build_knowledge_base(
    settings: Settings,
    embeddings: Embeddings,
) -> InMemoryVectorStore:
    """Load, chunk, and index the configured documents into an in-memory store.

    :param settings: Application settings providing the documents directory and
        the chunk size and overlap.
    :type settings: Settings
    :param embeddings: Embedding model used to vectorise the chunks.
    :type embeddings: Embeddings
    :returns: A vector store populated with the document chunks.
    :rtype: InMemoryVectorStore
    :raises KnowledgeBaseError: If the directory cannot be read, contains no
        Markdown documents, the chunking configuration is invalid, or indexing
        fails.
    """
    documents_dir = settings.documents_dir
    try:
        documents = load_markdown_documents(documents_dir)
    except (OSError, DocumentLoadError) as exc:
        raise KnowledgeBaseError(
            f"Could not load documents from {documents_dir}."
        ) from exc
    if not documents:
        raise KnowledgeBaseError(f"No Markdown documents found in {documents_dir}.")
    logger.info("Loaded %d document(s) from %s", len(documents), documents_dir)

    try:
        chunks = split_documents(
            documents,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except ValueError as exc:
        raise KnowledgeBaseError("Invalid chunk size or chunk overlap.") from exc
    logger.info(
        "Split documents into %d chunk(s) (size=%d, overlap=%d)",
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )

    store = create_in_memory_vector_store(embeddings)
    try:
        index_documents(store, chunks)
    except IndexingError as exc:
        raise KnowledgeBaseError("Failed to index document chunks.") from exc
    return store
