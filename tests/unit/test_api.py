"""Unit tests for the HTTP API using FastAPI's test client."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings.fake import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.api import dependencies
from app.api.dependencies import get_question_service
from app.main import app
from app.rag.graph import RAGGenerationError
from app.rag.retrieval import RAGRetrievalError
from app.services.question_service import QuestionService

SOURCE = Document(
    page_content="RAGdoll uses FastAPI for its HTTP API.",
    metadata={"source": "overview.md", "section": "Stack", "page": 1},
)


def _service(workflow: RunnableLambda) -> QuestionService:
    return QuestionService(workflow)


def _ok_service(answer: str, documents: list[Document]) -> QuestionService:
    return _service(
        RunnableLambda(lambda state: {"answer": answer, "documents": documents})
    )


def _failing_service(error: Exception) -> QuestionService:
    def fail(state: dict[str, Any]) -> dict[str, Any]:
        raise error

    return _service(RunnableLambda(fail))


@pytest.fixture
def override_service() -> Iterator[Any]:
    """Yield a setter that overrides the question service dependency."""

    def set_service(service: QuestionService) -> None:
        app.dependency_overrides[get_question_service] = lambda: service

    yield set_service
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_reports_ok_without_building_question_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_if_called() -> None:
        raise AssertionError("health must not build the question service")

    monkeypatch.setattr(dependencies, "create_chat_model", fail_if_called)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_question_returns_answer_and_source_metadata(
    client: TestClient, override_service: Any
) -> None:
    override_service(_ok_service("RAGdoll uses FastAPI.", [SOURCE]))

    response = client.post(
        "/api/v1/questions", json={"question": "Which web framework?"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "RAGdoll uses FastAPI.",
        "sources": [
            {
                "document_name": "overview.md",
                "section": "Stack",
                "content": "RAGdoll uses FastAPI for its HTTP API.",
                "metadata": {"source": "overview.md", "section": "Stack", "page": 1},
            }
        ],
    }


def test_question_is_stripped_before_answering(
    client: TestClient, override_service: Any
) -> None:
    received: list[dict[str, Any]] = []

    def capture(state: dict[str, Any]) -> dict[str, Any]:
        received.append(state)
        return {"answer": "ok", "documents": []}

    override_service(_service(RunnableLambda(capture)))

    client.post("/api/v1/questions", json={"question": "  Which framework?  "})

    assert received == [{"question": "Which framework?"}]


def test_empty_retrieval_returns_200_with_no_sources(
    client: TestClient, override_service: Any
) -> None:
    override_service(_ok_service("I could not find any relevant information.", []))

    response = client.post("/api/v1/questions", json={"question": "Unknown?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert "could not find" in response.json()["answer"]


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "   "},
        {},
        {"question": None},
        {"question": 42},
        {"question": "x" * 2001},
    ],
)
def test_invalid_question_is_rejected_with_422(
    client: TestClient, override_service: Any, payload: dict[str, Any]
) -> None:
    override_service(_ok_service("unused", []))

    response = client.post("/api/v1/questions", json=payload)

    assert response.status_code == 422


def test_generation_failure_returns_502_without_internal_details(
    client: TestClient, override_service: Any
) -> None:
    override_service(_failing_service(RAGGenerationError("Answer generation failed.")))

    response = client.post("/api/v1/questions", json={"question": "question"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The language model failed to generate an answer."
    }


def test_retrieval_failure_returns_503(
    client: TestClient, override_service: Any
) -> None:
    override_service(_failing_service(RAGRetrievalError("Document retrieval failed.")))

    response = client.post("/api/v1/questions", json={"question": "question"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Document retrieval is currently unavailable."}


def test_unexpected_error_returns_generic_500(
    client: TestClient, override_service: Any
) -> None:
    override_service(_failing_service(RuntimeError("secret sk-leaked-value")))

    response = client.post("/api/v1/questions", json={"question": "question"})

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
    assert "sk-leaked-value" not in response.text


@pytest.fixture
def reset_service_cache() -> Iterator[None]:
    get_question_service.cache_clear()
    yield
    get_question_service.cache_clear()


@pytest.mark.usefixtures("clean_settings_env", "reset_service_cache")
def test_missing_api_key_returns_503_without_exposing_configuration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    response = client.post("/api/v1/questions", json={"question": "question"})

    assert response.status_code == 503
    assert response.json() == {"detail": "The question service is not available."}
    assert "OPENAI_API_KEY" not in response.text


@pytest.mark.usefixtures("clean_settings_env", "reset_service_cache")
def test_default_wiring_answers_with_empty_store(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real wiring runs end to end with local fakes for the model and embeddings."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        dependencies,
        "create_chat_model",
        lambda settings: GenericFakeChatModel(messages=iter([AIMessage("unused")])),
    )
    monkeypatch.setattr(
        dependencies,
        "create_embeddings",
        lambda settings: DeterministicFakeEmbedding(size=8),
    )

    response = client.post("/api/v1/questions", json={"question": "Anything?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert "could not find" in response.json()["answer"]
