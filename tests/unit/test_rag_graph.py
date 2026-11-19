"""Unit tests for the core RAG workflow, using fake retriever and chat model."""

from typing import Any

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from app.rag.graph import RAGGenerationError, build_rag_graph
from app.rag.retrieval import RAGRetrievalError, create_retrieval_node
from app.rag.state import RAGState

DOCUMENTS = [
    Document(
        page_content="RAGdoll uses FastAPI.",
        metadata={"source": "overview.md", "page": 1},
    ),
    Document(
        page_content="Solver output is written to .pos files.",
        metadata={"source": "data_formats.md", "page": 4},
    ),
]


class FakeRetriever(BaseRetriever):
    """Retriever that returns a fixed list of documents and records queries."""

    documents: list[Document] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)

    def _get_relevant_documents(
        self, query: str, *, run_manager: Any
    ) -> list[Document]:
        self.queries.append(query)
        return list(self.documents)


class FailingRetriever(BaseRetriever):
    """Retriever whose lookup always raises a connection error."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: Any
    ) -> list[Document]:
        raise ConnectionError("vector store unavailable")


class FakeChatModel(BaseChatModel):
    """Chat model that records received messages and returns a fixed reply.

    Set ``error`` to make generation raise instead of replying.
    """

    reply: str = "fake answer"
    error: Exception | None = None
    received: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.received.append(messages)
        if self.error is not None:
            raise self.error
        return ChatResult(generations=[ChatGeneration(message=AIMessage(self.reply))])


def _state(documents: list[Document] | None = None) -> RAGState:
    return {
        "question": "What web framework does RAGdoll use?",
        "documents": documents or [],
        "answer": "",
    }


def test_retrieval_node_returns_documents_for_question() -> None:
    retriever = FakeRetriever(documents=DOCUMENTS)
    node = create_retrieval_node(retriever)

    update = node(_state())

    assert update == {"documents": DOCUMENTS}
    assert retriever.queries == ["What web framework does RAGdoll use?"]


def test_retriever_exception_is_raised_as_retrieval_error() -> None:
    graph = build_rag_graph(FailingRetriever(), FakeChatModel())

    with pytest.raises(RAGRetrievalError) as exc_info:
        graph.invoke({"question": "question"})

    assert isinstance(exc_info.value.__cause__, ConnectionError)


def test_graph_generates_answer_from_question_and_retrieved_context() -> None:
    chat_model = FakeChatModel(reply="RAGdoll uses FastAPI.")
    graph = build_rag_graph(FakeRetriever(documents=DOCUMENTS), chat_model)

    result = graph.invoke({"question": "What web framework does RAGdoll use?"})

    assert result["answer"] == "RAGdoll uses FastAPI."
    prompt_text = "\n".join(str(message.content) for message in chat_model.received[0])
    assert "What web framework does RAGdoll use?" in prompt_text
    assert "RAGdoll uses FastAPI." in prompt_text
    assert "Solver output is written to .pos files." in prompt_text


def test_graph_returns_source_documents_with_metadata() -> None:
    graph = build_rag_graph(FakeRetriever(documents=DOCUMENTS), FakeChatModel())

    result = graph.invoke({"question": "question"})

    assert result["documents"] == DOCUMENTS
    assert [doc.metadata for doc in result["documents"]] == [
        {"source": "overview.md", "page": 1},
        {"source": "data_formats.md", "page": 4},
    ]


def test_graph_does_not_fabricate_answer_when_nothing_is_retrieved() -> None:
    chat_model = FakeChatModel()
    graph = build_rag_graph(FakeRetriever(documents=[]), chat_model)

    result = graph.invoke({"question": "unknown topic"})

    assert result["documents"] == []
    assert "could not find" in result["answer"].lower()
    assert chat_model.received == []


def test_graph_raises_generation_error_when_chat_model_fails() -> None:
    chat_model = FakeChatModel(error=ConnectionError("provider unavailable"))
    graph = build_rag_graph(FakeRetriever(documents=DOCUMENTS), chat_model)

    with pytest.raises(RAGGenerationError) as exc_info:
        graph.invoke({"question": "question"})

    assert isinstance(exc_info.value.__cause__, ConnectionError)
