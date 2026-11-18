"""HTTP API routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.documents import Document

from app.api.dependencies import get_question_service
from app.api.schemas import QuestionRequest, QuestionResponse, SourceDocument
from app.services.question_service import (
    GenerationFailedError,
    QuestionService,
    RetrievalFailedError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["questions"])

QuestionServiceDep = Annotated[QuestionService, Depends(get_question_service)]


def _to_source(document: Document) -> SourceDocument:
    """Convert a retrieved document into an API source entry.

    :param document: A document returned by the RAG workflow.
    :type document: Document
    :returns: The source with its name and section taken from the metadata.
    :rtype: SourceDocument
    """
    metadata = dict(document.metadata)
    source = metadata.get("source")
    section = metadata.get("section")
    return SourceDocument(
        document_name=str(source) if source is not None else None,
        section=str(section) if section is not None else None,
        content=document.page_content,
        metadata=metadata,
    )


@router.post(
    "/questions",
    response_model=QuestionResponse,
    summary="Answer a question using the indexed documents",
    responses={
        422: {"description": "The request is missing the question or it is empty."},
        500: {"description": "An unexpected error occurred."},
        502: {"description": "The language model failed to generate an answer."},
        503: {"description": "Retrieval or the question service is unavailable."},
    },
)
def ask_question(
    request: QuestionRequest,
    service: QuestionServiceDep,
) -> QuestionResponse:
    """Answer a question and return the answer with its source documents.

    When no relevant documents are found, the response has an empty ``sources``
    list and an answer stating that the information is not available.

    :param request: The validated question.
    :type request: QuestionRequest
    :param service: The question service, injected by FastAPI.
    :type service: QuestionService
    :returns: The answer and its sources.
    :rtype: QuestionResponse
    :raises HTTPException: With status 502 if generation fails, 503 if
        retrieval fails, or 500 for any other unexpected error.
    """
    try:
        result = service.answer(request.question)
    except RetrievalFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is currently unavailable.",
        ) from exc
    except GenerationFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model failed to generate an answer.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error while answering a question")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from exc

    return QuestionResponse(
        answer=result.answer,
        sources=[_to_source(document) for document in result.documents],
    )
