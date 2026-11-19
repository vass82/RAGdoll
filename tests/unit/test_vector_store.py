"""Unit tests for the in-memory vector store and its integration with the RAG graph."""

from langchain_core.documents import Document
from langchain_core.embeddings.fake import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.infrastructure.vector_store import create_in_memory_vector_store
from app.rag.graph import build_rag_graph

DOCUMENTS = [
    Document(
        page_content="RAGdoll uses FastAPI for its HTTP API.",
        metadata={"source": "overview.md", "page": 1},
    ),
    Document(
        page_content="Solver output is written to .pos files.",
        metadata={"source": "data_formats.md", "page": 4},
    ),
]


def _embeddings() -> DeterministicFakeEmbedding:
    return DeterministicFakeEmbedding(size=32)


def test_documents_are_indexed_and_most_similar_is_retrieved() -> None:
    store = create_in_memory_vector_store(_embeddings(), DOCUMENTS)

    results = store.as_retriever(search_kwargs={"k": 1}).invoke(
        "Solver output is written to .pos files."
    )

    assert [doc.page_content for doc in results] == [
        "Solver output is written to .pos files."
    ]


def test_metadata_is_preserved_on_retrieval() -> None:
    store = create_in_memory_vector_store(_embeddings(), DOCUMENTS)

    results = store.as_retriever(search_kwargs={"k": 2}).invoke("RAGdoll uses FastAPI.")

    metadata_by_text = {doc.page_content: doc.metadata for doc in results}
    assert metadata_by_text == {
        "RAGdoll uses FastAPI for its HTTP API.": {"source": "overview.md", "page": 1},
        "Solver output is written to .pos files.": {
            "source": "data_formats.md",
            "page": 4,
        },
    }


def test_store_can_be_created_empty_and_populated_later() -> None:
    store = create_in_memory_vector_store(_embeddings())
    assert store.as_retriever().invoke("anything") == []

    store.add_documents(DOCUMENTS)

    assert len(store.as_retriever(search_kwargs={"k": 5}).invoke("anything")) == 2


def test_in_memory_retriever_feeds_rag_graph_with_source_metadata() -> None:
    store = create_in_memory_vector_store(_embeddings(), DOCUMENTS)
    chat_model = GenericFakeChatModel(messages=iter([AIMessage("FastAPI.")]))
    graph = build_rag_graph(store.as_retriever(search_kwargs={"k": 1}), chat_model)

    result = graph.invoke({"question": "RAGdoll uses FastAPI for its HTTP API."})

    assert result["answer"] == "FastAPI."
    assert result["documents"][0].metadata == {"source": "overview.md", "page": 1}
