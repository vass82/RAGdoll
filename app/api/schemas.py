"""Request and response schemas for the HTTP API."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_QUESTION_LENGTH = 2000

QuestionText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=MAX_QUESTION_LENGTH,
    ),
]


class QuestionRequest(BaseModel):
    """Request body for asking a question.

    :ivar question: The question to answer. Surrounding whitespace is removed,
        and the question must be non-empty after stripping.
    """

    question: QuestionText = Field(
        description="The question to answer.",
        examples=["Which web framework does RAGdoll use?"],
    )


class SourceDocument(BaseModel):
    """A retrieved document that supported the answer.

    :ivar document_name: The source file name, if recorded in the metadata.
    :ivar section: The section within the document, if recorded in the metadata.
    :ivar content: The text of the retrieved passage.
    :ivar metadata: All metadata stored with the document.
    """

    model_config = ConfigDict(extra="forbid")

    document_name: str | None = None
    section: str | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionResponse(BaseModel):
    """Response body containing the answer and the sources it was based on.

    :ivar answer: The generated answer.
    :ivar sources: Retrieved documents used to produce the answer. Empty when
        no relevant documents were found.
    """

    answer: str
    sources: list[SourceDocument]
