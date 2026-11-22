.. _rag_frameworks:

Frameworks: LangChain and LangGraph
===================================

RAGdoll is built on two libraries from the LangChain ecosystem. LangChain supplies
the building blocks: document loaders, text splitters, embeddings, vector
stores, retrievers, prompts, and chat models. LangGraph supplies the workflow
that connects them. This page explains what each library provides, how RAGdoll
uses them, and why a graph was chosen even though the current workflow is
linear.

What LangChain provides
-----------------------

LangChain is a set of Python packages that provide standard interfaces for the
components of an LLM application. Its main benefit is that the components are
interchangeable. Switching from one chat model to another, or from one vector
store to another, requires a different constructor but the same calling code.

The packages used by RAGdoll, with the minimum versions declared in
``pyproject.toml``, are:

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Package
     - Minimum
     - Role in RAGdoll
   * - ``langchain-core``
     - (transitive)
     - Base interfaces: documents, embeddings, vector stores, retrievers, prompts,
       and the ``Runnable`` protocol.
   * - ``langchain``
     - 1.5.0
     - The umbrella package for application-level utilities.
   * - ``langchain-text-splitters``
     - 1.1.3
     - ``RecursiveCharacterTextSplitter`` for chunking.
   * - ``langchain-huggingface``
     - 1.2.3
     - ``HuggingFaceEmbeddings`` for the local embedding model.
   * - ``langchain-openai``
     - 1.8.0
     - Chat model for the OpenAI API.
   * - ``langchain-ollama``
     - 1.1.0
     - Chat model for a local Ollama server.

The ``Runnable`` protocol is the important idea. Prompts, chat models, and
output parsers all expose the same ``invoke`` method and can be joined with the
``|`` operator. RAGdoll's generation node uses this to build its chain:

.. code-block:: python

   chain = GENERATION_PROMPT | chat_model | StrOutputParser()
   answer = chain.invoke({"context": context, "question": question})

The chain is a pipeline: the prompt output feeds the model, and the model output
feeds the parser. See :ref:`rag_generation` for the full node.

What LangGraph adds
-------------------

LangGraph is a library for building stateful workflows as graphs. A workflow is
described as:

* a **state** schema, a typed dictionary shared by all steps;
* **nodes**, functions that read the state and return an update to it;
* **edges**, which define the order in which nodes run, including conditional
  edges that choose the next node from the state.

The compiled graph can be invoked, streamed, and inspected. It also supports
features that matter for larger applications, such as persistence of state,
checkpoints, and human-in-the-loop pauses. RAGdoll uses none of these advanced
features today. It uses the basic state, nodes, and edges.

RAGdoll's state is defined in ``app/rag/state.py``. It holds the question, the
retrieved documents, and the answer. The graph is built and compiled in
:func:`~app.rag.graph.build_rag_graph`:

.. literalinclude:: ../../../app/rag/graph.py
   :pyobject: build_rag_graph
   :language: python

The graph is linear, ``START -> retrieval -> generation -> END``. Each node
receives the state and returns only the fields it changes. The retrieval node
adds ``documents``, and the generation node adds ``answer``.

Why RAGdoll uses LangGraph
--------------------------

A linear pipeline could be written as three function calls. LangGraph is used
for three reasons:

1. **Explicit state.** Each step reads and writes named fields, so the data
   that flows through the workflow is visible in one place. The returned
   ``documents`` field is also how the API obtains its sources.
2. **A place for growth.** The current graph is a starting point. A realistic
   extension would add nodes such as query rewriting, reranking, a relevance
   check that falls back to a web search, or a loop that retries retrieval with
   a new query. Conditional edges express these without changing the existing
   nodes.
3. **Testability.** Each node is a plain function that can be tested with a fake
   retriever or a fake chat model. The graph is compiled once and reused.

The trade-off is a small amount of framework overhead and a second library to
learn. For a single linear step, the benefit is modest, which is why the current
graph is kept deliberately simple.

Dependency injection in the graph
---------------------------------

``build_rag_graph`` takes the retriever and the chat model as arguments, rather
than creating them. This keeps the workflow independent of any vector store or
LLM provider. The concrete choices are made in the dependency layer.
:func:`~app.infrastructure.llm.create_chat_model` selects the chat model from the
``llm_provider`` setting:

* ``openai`` selects the OpenAI chat model named by ``openai_model``.
* ``ollama`` selects a local model named by ``ollama_model`` at
  ``ollama_base_url``.

The retriever and the chat model are assembled once per process by
``get_question_service``, which is discussed in
:ref:`concurrency_and_scalability`.

Alternatives
------------

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Option
     - Strength
     - When it fits
   * - Plain Python functions
     - No dependency beyond LangChain, easy to read.
     - A fixed pipeline with no branching.
   * - LangChain LCEL chains
     - Concise composition with ``|``.
     - Linear or simply branching pipelines.
   * - LangGraph
     - Explicit state, conditional edges, loops, persistence.
     - Workflows that branch, loop, or must resume after a pause.
   * - LlamaIndex
     - Strong data ingestion and indexing abstractions.
     - Document-centric applications that focus on indexing.

Further reading
---------------

* LangChain documentation: https://docs.langchain.com/
* LangChain RAG concepts: https://docs.langchain.com/oss/python/langchain/rag
* LangGraph documentation: https://langchain-ai.github.io/langgraph/
