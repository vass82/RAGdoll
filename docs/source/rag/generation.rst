.. _rag_generation:

Generation
==========

Generation is the last step of RAG. The retrieved chunks are placed into a
prompt, the LLM writes an answer from that prompt, and the chunks are returned
alongside the answer as sources. This page explains how that prompt is built,
what *grounded* generation means, the limits set by the context window, and why
sources matter.

Passing retrieved context to an LLM
-----------------------------------

An LLM receives only the text in its prompt. It does not query the knowledge
base itself. RAG therefore works by putting the relevant text into the prompt
before the model answers. The sequence for each question is:

1. Retrieve the top-k chunks for the question (see :ref:`rag_vector_stores`).
2. Format the chunks into one context string.
3. Insert the context and the question into a prompt template.
4. Send the prompt to the chat model and read the answer.

Prompt construction
-------------------

RAGdoll's prompt has two parts. The system message sets the behaviour, and the
human message supplies the context and the question. The constants are defined
in ``app/rag/prompts.py``:

.. literalinclude:: ../../../app/rag/prompts.py
   :start-at: GENERATION_SYSTEM_PROMPT = (
   :end-before: def format_context
   :language: python

The context is built by joining the page content of each chunk with a visible
separator, so the model can see where one chunk ends and the next begins:

.. literalinclude:: ../../../app/rag/prompts.py
   :pyobject: format_context
   :language: python

Several details of this design matter in practice:

* The instructions appear in the system message, and the untrusted text (the
  retrieved chunks and the user's question) appears in the human message.
* The prompt tells the model to refuse rather than guess when the context is
  insufficient. This is an instruction, not a guarantee. A model can still
  ignore it, so it should be tested against questions the knowledge base cannot
  answer.
* Only the page content is included in the prompt. Metadata such as the source
  file is not shown to the model. It is returned to the client separately.

Grounded generation
-------------------

*Grounded* generation means that the answer is based on the supplied context
rather than on the model's memory. Grounding is what turns a general chat model
into a documentation assistant. It does not make the answer correct. The answer
can still be wrong if:

* the retrieved chunks do not contain the answer (retrieval failure);
* the chunks contain the answer, but the model misreads or mixes them;
* the model fills a gap with its own knowledge despite the instruction.

For this reason RAG answers should be checked against the sources they cite.

Context window limitations
--------------------------

Every LLM has a *context window*, the maximum number of tokens it can read in
one request. The window must hold the system prompt, the context, the question,
and the answer. The context must therefore be small enough to fit, and it is
limited by ``k`` times the chunk size.

With RAGdoll's defaults, four chunks of up to 1000 characters add roughly one
thousand tokens of context. That is well inside the window of common models,
but the limit becomes significant with larger chunks or larger ``k``.

Research also shows that models do not use all of a long context equally well.
Liu et al. report that relevant information placed in the middle of a long
prompt is used less reliably than information placed at the beginning or end
(*Lost in the Middle*, https://arxiv.org/abs/2307.03172). This is a reason to
keep ``k`` modest and to rank the most relevant chunks first, as the retriever
does.

The generation node
-------------------

In RAGdoll, the generation step is a LangGraph node. It composes the prompt,
the chat model, and an output parser into a chain, and it is the only place
where the chat model is called:

.. literalinclude:: ../../../app/rag/graph.py
   :pyobject: create_generation_node
   :language: python

If retrieval returns no documents, the node returns a fixed message and does not
call the model. This prevents the LLM from answering from its own memory when
the knowledge base has nothing relevant. The graph that connects this node to
retrieval is built by ``build_rag_graph``:

.. literalinclude:: ../../../app/rag/graph.py
   :pyobject: build_rag_graph
   :language: python

Returning sources
-----------------

Returning sources means that the response includes the retrieved chunks, not
only the answer. This allows a user to check the claim against the original
text. It is also how the application builds traceability, because each source
carries the metadata created during ingestion (see
:ref:`rag_document_processing`).

RAGdoll's HTTP response returns each source with its ``document_name``,
``section``, ``content``, and ``metadata``. The mapping from retrieved documents
to the response is done in the route layer. The ``section`` field is part of
that response but is not populated by the current loader, so it is always
``null`` in production.

Failure modes
-------------

The generation step has two distinct failures, and they are reported
differently:

* If the chat model cannot be reached or raises an error, the node raises
  ``RAGGenerationError``, which the API reports as an upstream failure (HTTP 502).
* If there is no context, the node returns ``NO_CONTEXT_ANSWER`` without calling
  the model. This is a normal answer, not an error.

Further reading
---------------

* LangChain RAG tutorial and concepts:
  https://python.langchain.com/docs/tutorials/rag/
* Liu et al., *Lost in the Middle: How Language Models Use Long Contexts* (2023):
  https://arxiv.org/abs/2307.03172
* OpenAI, *Prompt engineering* guide:
  https://platform.openai.com/docs/guides/prompt-engineering
