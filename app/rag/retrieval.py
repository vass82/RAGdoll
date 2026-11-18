"""Document retrieval for the RAG workflow."""

from collections.abc import Callable

from langchain_core.retrievers import BaseRetriever

from app.rag.state import RAGState


class RAGRetrievalError(RuntimeError):
    """Raised when the retriever fails to return documents."""


def create_retrieval_node(retriever: BaseRetriever) -> Callable[[RAGState], dict]:
    """Create a LangGraph node that retrieves documents for the state's question.

    The retriever is injected so the node does not depend on any specific
    vector store or embedding provider.

    :param retriever: Any LangChain retriever that maps a query to documents.
    :type retriever: BaseRetriever
    :returns: A node function that returns the ``documents`` state update.
    :rtype: Callable[[RAGState], dict]
    """

    def retrieve(state: RAGState) -> dict:
        """Retrieve documents relevant to the question in the state.

        :param state: The current workflow state.
        :type state: RAGState
        :returns: A partial state update containing the retrieved documents.
        :rtype: dict
        :raises RAGRetrievalError: If the retriever raises an exception.
        """
        try:
            documents = retriever.invoke(state["question"])
        except Exception as exc:
            raise RAGRetrievalError("Document retrieval failed.") from exc
        return {"documents": documents}

    return retrieve
