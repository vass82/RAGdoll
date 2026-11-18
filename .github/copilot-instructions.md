Project context

RAGdoll is a Python backend application implementing a simple Retrieval-Augmented Generation (RAG) pipeline. It uses FastAPI for the HTTP API and LangChain/LangGraph for the RAG workflow.

The primary goal is to demonstrate sound software engineering, clear architecture, testability, and reliable integration—not to build an unnecessarily sophisticated AI system.
General development principles

    Follow the existing project structure and conventions.

    Prefer simple, readable, maintainable solutions over unnecessary abstractions.

    Avoid overengineering and premature optimization.

    Keep API, application logic, RAG workflow, infrastructure integrations, and configuration responsibilities separate.

    Make external dependencies injectable wherever practical, so components can be tested independently.

    Avoid introducing new dependencies unless they are genuinely necessary.

    Before using a library API, check the installed dependency versions and use compatible APIs. Do not assume that examples from older LangChain versions still apply.

    Do not introduce ChromaDB or another persistent vector database unless explicitly requested.

    Do not introduce cloud infrastructure or paid services as requirements for local development or testing.

Documentation conventions

Use reStructuredText (reST) style for Python docstrings.

For functions and methods, document relevant parameters, return values, and exceptions using the following conventions:

    :param parameter_name:

    :type parameter_name:

    :returns:

    :rtype:

    :raises ExceptionType:

For example:

def retrieve_documents(question: str) -> list[Document]:
    """Retrieve documents relevant to the supplied question.

    :param question: The user's question.
    :type question: str
    :returns: A list of relevant documents.
    :rtype: list[Document]
    """

Use meaningful module, class, and function docstrings. Avoid documenting obvious implementation details or adding verbose comments that simply repeat the code.
Testing conventions

    Use pytest.

    Keep unit tests independent of external services and API keys.

    Use mocks or lightweight fakes for external integrations.

    Test expected behaviour, edge cases, and failure paths.

    Do not make real LLM or embedding API calls in the normal CI test suite.

    Keep tests readable and avoid excessive mocking of internal implementation details.

Code quality

    Follow the existing Ruff configuration.

    Use Python 3.12-compatible syntax.

    Add type annotations to public functions and methods.

    Keep functions reasonably small and focused.

    Handle errors explicitly rather than silently swallowing exceptions.

    Do not expose secrets or sensitive configuration in logs or API responses.

