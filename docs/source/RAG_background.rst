.. _RAG_background:

RAG Background
==============

This section explains the theory behind RAGdoll from first principles. It is
written so that a reader with basic Python knowledge but no prior RAG experience
can follow it, and it is organised so that each topic can also be reviewed on
its own when preparing for a technical interview.

The pages are:

.. toctree::
   :maxdepth: 1

   rag/fundamentals
   rag/document_processing
   rag/embeddings
   rag/vector_stores
   rag/generation
   rag/retrieval_quality
   rag/frameworks
   rag/rag_faq

.. _rag_end_to_end:

End-to-end workflow
-------------------

A RAG system has an *offline* part, which prepares the knowledge base, and an
*online* part, which answers each question. RAGdoll implements both.

.. code-block:: text

   OFFLINE: indexing (once per process in RAGdoll)

   documents --> load --> split into chunks --> embed each chunk --> vector store
   (Markdown)   (metadata)  (size, overlap)      (vector per chunk)   (chunk + vector + metadata)

   ONLINE: answering (each question)

   question --> embed question --> similarity search --> top-k chunks
                                                              |
                 prompt = instructions + chunks + question <--+
                                    |
                                    v
                     LLM --> answer + the chunks used as sources

The offline and online parts must agree on one thing: the **embedding model**.
The same model must turn both the chunks and the question into vectors, or the
similarity scores are meaningless (see :ref:`rag_embeddings`).

In RAGdoll the online steps are the two nodes of the LangGraph workflow in
:mod:`app.rag.graph`, ``retrieval`` followed by ``generation``. The offline
steps are the functions in :mod:`app.services.knowledge_base`.

Further reading
---------------

* Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP
  Tasks* (2020), the paper that introduced the term: https://arxiv.org/abs/2005.11401
* The LangChain documentation on RAG: https://docs.langchain.com/oss/python/langchain/rag
