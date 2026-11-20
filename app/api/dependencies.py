"""Dependency wiring that builds the question service from application settings."""

import logging
from functools import lru_cache

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.infrastructure.embeddings import create_embeddings
from app.infrastructure.llm import create_chat_model
from app.rag.graph import build_rag_graph
from app.services.knowledge_base import KnowledgeBaseError, build_knowledge_base
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)


@lru_cache
def get_question_service() -> QuestionService:
    """Return the process-wide question service, building it on first use.

    The documents are loaded, chunked, and indexed once per process, when the
    service is first built. The chat model, embeddings, and populated
    in-memory knowledge base are compiled into the RAG graph. A failed build is
    not cached, so the next request retries it; a partially indexed store is
    never returned. Failures are logged without configuration values.

    :returns: The configured question service.
    :rtype: QuestionService
    :raises HTTPException: With status 503 if the language model, embeddings,
        or knowledge base cannot be initialised.
    """
    settings = get_settings()
    try:
        chat_model = create_chat_model(settings)
        embeddings = create_embeddings(settings)
        store = build_knowledge_base(settings, embeddings)
        return QuestionService(build_rag_graph(store.as_retriever(), chat_model))

    except Exception as exc:
        reason = str(exc) if isinstance(exc, KnowledgeBaseError) else type(exc).__name__
        logger.error("Question service initialisation failed: %s", reason)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The question service is not available.",
        ) from exc
