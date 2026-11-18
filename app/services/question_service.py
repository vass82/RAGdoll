"""Application service that answers questions using the RAG workflow."""

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document
from langchain_core.runnables import Runnable

from app.rag.graph import RAGGenerationError
from app.rag.retrieval import RAGRetrievalError

logger = logging.getLogger(__name__)


class QuestionServiceError(Exception):
    """Base class for errors raised while answering a question."""


class RetrievalFailedError(QuestionServiceError):
    """Raised when documents could not be retrieved for the question."""


class GenerationFailedError(QuestionServiceError):
    """Raised when the language model could not produce an answer."""


@dataclass(frozen=True)
class AnswerResult:
    """Result of answering a question.

    :ivar answer: The generated answer text.
    :ivar documents: The retrieved documents used as sources, with metadata.
    """

    answer: str
    documents: list[Document] = field(default_factory=list)


class QuestionService:
    """Answers questions by invoking an injected RAG workflow.

    The workflow is any LangChain runnable that accepts ``{"question": ...}``
    and returns a mapping with ``answer`` and ``documents``. Construct it with
    :func:`app.rag.graph.build_rag_graph` or a compatible fake in tests.
    """

    def __init__(self, workflow: Runnable[dict[str, Any], dict[str, Any]]) -> None:
        """Initialise the service with its RAG workflow.

        :param workflow: The compiled RAG workflow to execute for each question.
        :type workflow: Runnable[dict[str, Any], dict[str, Any]]
        """
        self._workflow = workflow

    def answer(self, question: str) -> AnswerResult:
        """Run the RAG workflow for a question and return the answer with sources.

        :param question: The user's question. Must already be validated.
        :type question: str
        :returns: The generated answer and the documents it was based on.
        :rtype: AnswerResult
        :raises RetrievalFailedError: If document retrieval fails.
        :raises GenerationFailedError: If the language model fails.
        """
        try:
            state = self._workflow.invoke({"question": question})
        except RAGRetrievalError as exc:
            logger.error("Retrieval failed: %s", type(exc.__cause__).__name__)
            raise RetrievalFailedError("Document retrieval failed.") from exc
        except RAGGenerationError as exc:
            logger.error("Generation failed: %s", type(exc.__cause__).__name__)
            raise GenerationFailedError("Answer generation failed.") from exc

        documents = list(state.get("documents", []))
        logger.info(
            "Answered question of length %d using %d source(s)",
            len(question),
            len(documents),
        )
        return AnswerResult(answer=state["answer"], documents=documents)
