"""In-memory vector store factory.

The store is kept in process memory and is lost on restart. It is intended as
the initial vector store; persistent storage is out of scope for now.
"""

from collections.abc import Iterable

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


def create_in_memory_vector_store(
    embeddings: Embeddings,
    documents: Iterable[Document] = (),
) -> InMemoryVectorStore:
    """Create an in-memory vector store and populate it with documents.

    Each document is embedded with ``embeddings`` on insertion. Document
    metadata is stored alongside the content and returned on retrieval.

    :param embeddings: Embedding model used to vectorise documents and queries.
    :type embeddings: Embeddings
    :param documents: Documents to index. May be empty.
    :type documents: Iterable[Document]
    :returns: The populated vector store. Use ``as_retriever()`` to obtain a
        retriever for the RAG graph.
    :rtype: InMemoryVectorStore
    """
    store = InMemoryVectorStore(embeddings)
    docs = list(documents)
    if docs:
        store.add_documents(docs)
    return store
