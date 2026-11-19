"""LangGraph workflow that answers questions from retrieved documents."""

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.rag.prompts import (
    GENERATION_PROMPT,
    NO_CONTEXT_ANSWER,
    format_context,
)
from app.rag.retrieval import create_retrieval_node
from app.rag.state import RAGState


class RAGGenerationError(RuntimeError):
    """Raised when the chat model fails to generate an answer."""


def create_generation_node(
    chat_model: BaseChatModel,
) -> Callable[[RAGState], dict]:
    """Create a LangGraph node that generates an answer from retrieved documents.

    If no documents were retrieved, the node returns a fixed message and does
    not call the chat model, so no answer is fabricated.

    :param chat_model: Any LangChain chat model.
    :type chat_model: BaseChatModel
    :returns: A node function that returns the ``answer`` state update.
    :rtype: Callable[[RAGState], dict]
    """
    chain = GENERATION_PROMPT | chat_model | StrOutputParser()

    def generate(state: RAGState) -> dict:
        """Generate an answer grounded in the retrieved documents.

        :param state: The current workflow state, with ``documents`` populated.
        :type state: RAGState
        :returns: A partial state update containing the generated answer.
        :rtype: dict
        :raises RAGGenerationError: If the chat model raises an exception.
        """
        documents = state["documents"]
        if not documents:
            return {"answer": NO_CONTEXT_ANSWER}

        try:
            answer = chain.invoke(
                {
                    "context": format_context(documents),
                    "question": state["question"],
                }
            )
        except Exception as exc:
            raise RAGGenerationError("Answer generation failed.") from exc
        return {"answer": answer}

    return generate


def build_rag_graph(
    retriever: BaseRetriever,
    chat_model: BaseChatModel,
) -> CompiledStateGraph:
    """Build and compile the RAG workflow ``START -> retrieval -> generation -> END``.

    :param retriever: Retriever used to fetch documents for the question.
    :type retriever: BaseRetriever
    :param chat_model: Chat model used to generate the answer.
    :type chat_model: BaseChatModel
    :returns: The compiled graph. Invoke it with ``{"question": ...}``; the
        result contains ``question``, ``documents`` (the sources), and ``answer``.
    :rtype: CompiledStateGraph
    """
    builder = StateGraph(RAGState)
    builder.add_node("retrieval", create_retrieval_node(retriever))
    builder.add_node("generation", create_generation_node(chat_model))
    builder.add_edge(START, "retrieval")
    builder.add_edge("retrieval", "generation")
    builder.add_edge("generation", END)
    return builder.compile()
