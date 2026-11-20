"""Indexing of document chunks into a vector store."""

import logging
from collections.abc import Sequence

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

logger = logging.getLogger(__name__)


class IndexingError(RuntimeError):
    """Raised when document chunks cannot be embedded or inserted into the store."""


def index_documents(store: VectorStore, documents: Sequence[Document]) -> int:
    """Embed and add document chunks to a vector store.

    Empty input is accepted and leaves the store untouched.

    :param store: The vector store to add the chunks to. Its embedding model
        is used to vectorise each chunk.
    :type store: VectorStore
    :param documents: The chunks to index. May be empty.
    :type documents: Sequence[Document]
    :returns: The number of chunks indexed.
    :rtype: int
    :raises IndexingError: If embedding or inserting the chunks fails.
    """
    if not documents:
        logger.info("No document chunks to index")
        return 0

    try:
        store.add_documents(list(documents))
    except Exception as exc:
        raise IndexingError("Failed to index document chunks.") from exc

    logger.info("Indexed %d document chunk(s)", len(documents))
    return len(documents)
