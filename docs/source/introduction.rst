.. _introduction:

Introduction
============

What RAGdoll is
---------------

**RAGdoll** is a Python backend for a *retrieval-augmented generation* (RAG)
question-answering service. A client sends a natural-language question to an
HTTP endpoint; the service searches a collection of Markdown documents for
passages relevant to the question, passes those passages to a large language
model (LLM), and returns the generated answer together with the passages it
was based on.

The repository is intentionally small. Its purpose is to demonstrate a clean
architecture for a RAG pipeline: a thin HTTP layer, an application service, a
LangGraph workflow, and replaceable infrastructure adapters for the language
model, the embedding model, and the vector store. It is not a production
system (see :ref:`intro_scope`).

The problem it solves
---------------------

Large language models answer from knowledge fixed at training time. They
cannot read a private or specialised document collection, they do not know
about information published after training, and when they do not know an
answer they may produce a fluent but incorrect one. This is the *hallucination*
problem discussed in :ref:`rag_fundamentals`.

RAGdoll addresses this by making the model answer from documents supplied at
query time. Each answer is:

* **grounded** in passages retrieved from the knowledge base,
* **traceable** because the response lists its source passages, and
* **updatable** by changing the documents rather than retraining a model.

The example knowledge base is a set of condensed Markdown summaries of the
GetDP finite-element solver documentation (see :ref:`getdp_documentation`).

Why Retrieval-Augmented Generation is useful
--------------------------------------------

RAG is attractive when an application needs answers that are specific to a
body of text the model was not trained on, and when those answers must be
verifiable. Typical examples are internal documentation search, product
support assistants, and scientific or legal question answering. Compared with
fine-tuning, RAG needs no model training, and the knowledge base can be changed
by editing files and re-indexing them. The :ref:`RAG background <RAG_background>`
explains the trade-offs in detail.

Intended users and use cases
----------------------------

RAGdoll is written for three audiences:

* **Developers learning RAG** who want a readable, working reference
  implementation of the main RAG components.
* **Engineers preparing for interviews** who need a concrete system to discuss
  when explaining chunking, embeddings, retrieval, and prompt construction.
* **Maintainers of the project**, who use the architecture as the basis for
  incremental features.

The main use case is asking questions of a set of Markdown documents through
the ``POST /api/v1/questions`` endpoint. The application is designed so that
the document folder can be replaced with a different domain.

Main technologies
-----------------

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Concern
     - Technology
     - Where it is used
   * - HTTP API
     - `FastAPI <https://fastapi.tiangolo.com/>`_, served by
       `Uvicorn <https://www.uvicorn.org/>`_
     - ``app/main.py``, ``app/api/``
   * - RAG workflow
     - `LangGraph <https://langchain-ai.github.io/langgraph/>`_ on top of
       `LangChain <https://docs.langchain.com/>`_ components
     - ``app/rag/graph.py``
   * - Document splitting
     - ``langchain-text-splitters``
     - ``app/rag/chunking.py``
   * - Embeddings
     - `Sentence Transformers <https://www.sbert.net/>`_ through
       ``langchain-huggingface``
     - ``app/infrastructure/embeddings.py``
   * - Vector store
     - LangChain ``InMemoryVectorStore``
     - ``app/infrastructure/vector_store.py``
   * - Language model
     - `OpenAI <https://platform.openai.com/>`_ (default) or
       `Ollama <https://ollama.com/>`_ (local)
     - ``app/infrastructure/llm.py``
   * - Configuration
     - `pydantic-settings <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_
     - ``app/core/config.py``
   * - Testing
     - pytest, HTTPX, Ruff
     - ``tests/``

The exact dependency versions are pinned in ``uv.lock``.

Architecture overview
---------------------

RAGdoll has two phases. The **knowledge base** is built once per process, when
the first question arrives. After that, each **question** reuses the in-memory
index and the compiled workflow.

Ingestion (first question request)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   data/documents/*.md
           |
           v
   load_markdown_documents()        app/infrastructure/document_loader.py
           |  one Document per non-empty file, with metadata
           v
   split_documents()                app/rag/chunking.py
           |  RecursiveCharacterTextSplitter (chunk_size, chunk_overlap)
           v
   index_documents() -> store       app/rag/indexing.py
           |  embeds each chunk with the embedding model
           v
   InMemoryVectorStore              app/infrastructure/vector_store.py

Question answering (each request)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   client
     |  POST /api/v1/questions {"question": "..."}
     v
   ask_question()                   app/api/routes.py
     |  Depends(get_question_service)  app/api/dependencies.py
     v
   QuestionService.answer()         app/services/question_service.py
     |  workflow.invoke({"question": ...})
     v
   LangGraph: START -> retrieval -> generation -> END   app/rag/graph.py
     |                    |
     |  retriever.invoke  |  GENERATION_PROMPT | chat_model | parser
     v                    v
   top-k chunks         answer grounded in the chunks
     |                    |
     +---------+----------+
               v
   QuestionResponse {answer, sources}   app/api/schemas.py

Component responsibilities
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Layer
     - Modules
     - Responsibility
   * - HTTP
     - ``app/main.py``, ``app/api/routes.py``, ``app/api/schemas.py``
     - Routing, request validation, and mapping errors to HTTP status codes.
       ``GET /health`` reports process liveness only.
   * - Dependency wiring
     - ``app/api/dependencies.py``
     - Builds the :class:`~app.services.question_service.QuestionService` once
       per process, on first use.
   * - Application services
     - ``app/services/``
     - Builds the knowledge base and runs the workflow for a question.
   * - RAG workflow
     - ``app/rag/``
     - The LangGraph graph, retrieval and generation nodes, prompts, and the
       chunking and indexing steps.
   * - Infrastructure
     - ``app/infrastructure/``
     - Adapters for the document loader, embedding model, chat model, and
       vector store.
   * - Configuration
     - ``app/core/config.py``
     - The :class:`~app.core.config.Settings` class, read from environment
       variables and ``.env``.

Dependencies are injected at the boundaries. For example,
:func:`~app.rag.graph.build_rag_graph` accepts any LangChain retriever and chat
model, so the tests can substitute deterministic fakes without network access.

The HTTP interface
^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Endpoint
     - Behaviour
   * - ``GET /health``
     - Returns ``{"status": "ok"}``. It does not contact the LLM or the
       embedding provider.
   * - ``POST /api/v1/questions``
     - Accepts ``{"question": "..."}`` and returns ``answer`` and ``sources``.
       Status codes: ``422`` for invalid input, ``503`` if initialisation or
       retrieval fails, ``502`` if generation fails, ``500`` for other errors.

.. _intro_scope:

Implemented and out of scope
----------------------------

The table below separates what the repository implements today from what is
deliberately left out. The latter are discussed as possible extensions in
:ref:`concurrency_and_scalability`.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Area
     - Implemented
     - Not implemented
   * - Documents
     - Recursive loading of ``.md`` files from ``DOCUMENTS_DIR``, with
       ``source`` and ``relative_path`` metadata.
     - Other formats (PDF, HTML, Office files), live connectors, and
       incremental re-indexing.
   * - Retrieval
     - Top-k cosine similarity search in memory (``k`` defaults to 4).
     - Metadata filtering, hybrid (keyword and vector) search, reranking, and
       query rewriting.
   * - Storage
     - Process-local, in-memory vector store rebuilt at first use.
     - A persistent or shared vector database. The README lists ChromaDB as a
       planned store, but it is not a dependency yet.
   * - Models
     - OpenAI or Ollama chat models; a local Sentence Transformers embedding
       model.
     - Streaming responses, conversation memory, and per-user API keys.
   * - API
     - One question endpoint, with sources in the response.
     - Authentication, rate limiting, request IDs, and metrics.
   * - Operations
     - A Dockerfile and a Compose file that run the backend on port 8000.
     - Multiple workers, a readiness probe, background ingestion, and
       production monitoring.

Reading guide
-------------

* To learn the RAG concepts behind the design, read :ref:`RAG_background`
  first.
* To understand the example dataset and why it was chosen, read
  :ref:`getdp_documentation`.
* To understand what would change under load, read
  :ref:`concurrency_and_scalability`.
* For the HTTP endpoints, see the :ref:`http_api` reference.
* For class and function details, see the :ref:`python_api` reference.