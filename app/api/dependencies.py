"""Dependency wiring that builds the question service from application settings."""

import logging
from functools import lru_cache

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.infrastructure.embeddings import create_embeddings
from app.infrastructure.llm import create_chat_model
from app.infrastructure.vector_store import create_in_memory_vector_store
from app.rag.graph import build_rag_graph
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)


@lru_cache
def get_question_service() -> QuestionService:
    """Return the process-wide question service, building it on first use.

    The chat model, embeddings, and in-memory vector store are created from
    the current settings and compiled into the RAG graph. Failures are logged
    by exception type only, so configuration values are never exposed.

    :returns: The configured question service.
    :rtype: QuestionService
    :raises HTTPException: With status 503 if the language model or embeddings
        cannot be initialised.
    """
    settings = get_settings()
    try:
        chat_model = create_chat_model(settings)
        embeddings = create_embeddings(settings)
        store = create_in_memory_vector_store(embeddings)
        return QuestionService(build_rag_graph(store.as_retriever(), chat_model))

    except Exception as exc:
        logger.error("Question service initialisation failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The question service is not available.",
        ) from exc
