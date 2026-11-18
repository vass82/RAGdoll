"""Unit tests for the question service."""

from typing import Any

import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from app.rag.graph import RAGGenerationError
from app.rag.retrieval import RAGRetrievalError
from app.services.question_service import (
    GenerationFailedError,
    QuestionService,
    RetrievalFailedError,
)

SOURCE = Document(
    page_content="RAGdoll uses FastAPI.",
    metadata={"source": "overview.md", "section": "Stack"},
)


def _workflow(result: dict[str, Any]) -> RunnableLambda:
    return RunnableLambda(lambda state: result)


def _failing_workflow(error: Exception) -> RunnableLambda:
    def fail(state: dict[str, Any]) -> dict[str, Any]:
        raise error

    return RunnableLambda(fail)


def test_answer_returns_answer_and_source_documents() -> None:
    service = QuestionService(_workflow({"answer": "FastAPI.", "documents": [SOURCE]}))

    result = service.answer("Which framework?")

    assert result.answer == "FastAPI."
    assert result.documents == [SOURCE]
    assert result.documents[0].metadata == {"source": "overview.md", "section": "Stack"}


def test_answer_passes_question_to_workflow() -> None:
    received: list[dict[str, Any]] = []

    def capture(state: dict[str, Any]) -> dict[str, Any]:
        received.append(state)
        return {"answer": "", "documents": []}

    service = QuestionService(RunnableLambda(capture))

    service.answer("Which framework?")

    assert received == [{"question": "Which framework?"}]


def test_answer_with_no_documents_returns_empty_sources() -> None:
    service = QuestionService(
        _workflow({"answer": "Not in the context.", "documents": []})
    )

    result = service.answer("Unknown topic?")

    assert result.documents == []
    assert result.answer == "Not in the context."


def test_retrieval_error_is_mapped_to_retrieval_failed_error() -> None:
    service = QuestionService(
        _failing_workflow(RAGRetrievalError("Document retrieval failed."))
    )

    with pytest.raises(RetrievalFailedError):
        service.answer("question")


def test_generation_error_is_mapped_to_generation_failed_error() -> None:
    service = QuestionService(
        _failing_workflow(RAGGenerationError("Answer generation failed."))
    )

    with pytest.raises(GenerationFailedError):
        service.answer("question")


def test_unexpected_error_propagates_unchanged() -> None:
    service = QuestionService(_failing_workflow(KeyError("boom")))

    with pytest.raises(KeyError):
        service.answer("question")
