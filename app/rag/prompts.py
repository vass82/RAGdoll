"""Prompts used by the RAG workflow."""

from collections.abc import Sequence

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

CONTEXT_SEPARATOR = "\n\n---\n\n"

NO_CONTEXT_ANSWER = (
    "I could not find any relevant information in the knowledge base to answer "
    "this question."
)

GENERATION_SYSTEM_PROMPT = (
    "You are a question-answering assistant. Answer the user's question using "
    "only the context provided in the user message.\n"
    "- Do not invent facts that are not supported by the context.\n"
    "- If the context does not contain enough information to answer, say so "
    "explicitly instead of guessing.\n"
    "- Be concise and accurate."
)

GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", GENERATION_SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


def format_context(documents: Sequence[Document]) -> str:
    """Join the text of retrieved documents into a single context string.

    :param documents: Documents returned by the retriever.
    :type documents: Sequence[Document]
    :returns: The page content of each document, separated by a delimiter.
    :rtype: str
    """
    return CONTEXT_SEPARATOR.join(doc.page_content for doc in documents)
