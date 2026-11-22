.. _python_api:

Python API reference
====================

The Python API reference is generated from the ``app`` package by
`sphinx-autoapi <https://sphinx-autoapi.readthedocs.io/>`_ during every build.
It is produced from the source code and its docstrings, so it always matches
the implementation. Do not edit the generated pages; change the docstrings or
the code instead.

The HTTP endpoints that expose part of this package are described separately in
:ref:`http_api`.

Module groups
-------------

The package is organised into the following groups. Each group has its own
page in the generated index below.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Group
     - Responsibility
   * - ``app.main``
     - The FastAPI application object and the ``/health`` endpoint.
   * - ``app.api``
     - HTTP routes, request and response schemas, and dependency wiring that
       builds the question service once per process.
   * - ``app.core``
     - Application settings loaded from environment variables and ``.env``.
   * - ``app.infrastructure``
     - Adapters for the Markdown document loader, the chat model (OpenAI or
       Ollama), the Sentence Transformers embeddings, and the in-memory vector
       store.
   * - ``app.rag``
     - The RAG workflow: chunking, indexing, retrieval, prompts, state, and the
       LangGraph graph that connects them.
   * - ``app.services``
     - The knowledge-base builder and the question service that runs the RAG
       workflow for each request.

.. toctree::
   :maxdepth: 2
   :caption: Generated modules:

   python-api/index
