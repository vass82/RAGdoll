"""State definition for the RAG workflow."""

from typing import TypedDict

from langchain_core.documents import Document


class RAGState(TypedDict):
    """Mutable state passed between nodes of the RAG graph.

    :ivar question: The user's question.
    :ivar documents: Documents retrieved for the question. Each document keeps
        its original metadata so it can be returned as an answer source.
    :ivar answer: The generated answer, or an empty string before generation.
    """

    question: str
    documents: list[Document]
    answer: str
