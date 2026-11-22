.. _rag_interview_questions:

Interview preparation
=====================

This page collects questions that are commonly asked about RAG and gives short
answers, with pointers to the sections above and to RAGdoll's code. The answers
are written to be spoken, and each one can be expanded with the material in
the earlier pages.

Fundamentals
------------

**What is RAG, and why use it instead of fine-tuning?**
   RAG retrieves relevant text at query time and places it in the prompt, so the
   model answers from supplied evidence. Fine-tuning changes the model's weights
   and is slow, costly, and hard to update. RAG can use new documents immediately
   and can cite its sources (see :ref:`rag_fundamentals`).

**What problems does RAG address?**
   Knowledge cut-off, where the model has no information after its training;
   hallucination, where the model invents plausible details; and the lack of
   private or domain data. RAG does not eliminate hallucination, but it gives the
   model evidence to ground its answer in.

**How does RAGdoll avoid answering when the knowledge base has nothing relevant?**
   The generation node checks whether retrieval returned any documents. If none
   were returned, it returns ``NO_CONTEXT_ANSWER`` without calling the model
   (see :ref:`rag_generation`).

Documents and chunking
----------------------

**Why split documents into chunks?**
   Embedding models have an input limit, retrieval should return focused text,
   and the context window is finite. Chunks are the unit that is embedded,
   retrieved, and sent to the model.

**How do you choose chunk size and overlap?**
   Choose them by measuring retrieval against a question set, not by intuition.
   Chunks that are too small lose context; chunks that are too large dilute the
   embedding and waste tokens. Overlap protects against splitting an answer at a
   boundary, at the cost of duplication. RAGdoll uses 1000 and 200 characters
   (see :ref:`rag_chunk_size_overlap`).

**Why keep metadata?**
   Metadata enables source citation, filtering, and debugging. RAGdoll stores
   ``source`` and ``relative_path`` with every chunk (see
   :ref:`rag_document_processing`).

Embeddings and similarity
-------------------------

**What is an embedding?**
   A fixed-length vector that represents the meaning of a text, so that texts
   with similar meaning are close in the vector space (see :ref:`rag_embeddings`).

**Why cosine similarity?**
   It compares direction and ignores length, which is usually what matters for
   text. For unit-length vectors it is equivalent to the dot product.

**Why must the same embedding model be used for indexing and querying?**
   Vectors from different models live in different spaces, so distances between
   them are meaningless. Changing the model requires re-indexing.

Vector stores
-------------

**What does a vector store do?**
   It stores vectors with their payloads and metadata, and returns the nearest
   vectors to a query. RAGdoll's store is an in-memory, brute-force, cosine
   search (see :ref:`rag_vector_stores`).

**What is top-k retrieval, and how do you choose k?**
   It returns the k most similar chunks. A larger k increases recall and cost and
   adds noise; a smaller k increases precision and risks missing context. RAGdoll
   uses ``k=4``.

**What is approximate nearest-neighbour search?**
   Index structures, such as HNSW or IVF, that find near neighbours without
   comparing every vector. They trade a small loss of recall for a large gain in
   speed. Exact search is adequate for small collections.

Generation
----------

**How is retrieved context passed to the model?**
   It is formatted into a single string and inserted into a prompt template with
   the question. The system message contains the grounding instructions.

**What does grounded generation mean, and does it guarantee correctness?**
   It means the answer is based on the supplied context. It does not guarantee
   correctness, because retrieval can miss the answer or the model can misread it.

**Why return sources?**
   So that users can verify the answer against the original text, and so that
   errors can be traced to a specific chunk.

Retrieval quality
-----------------

**What are precision and recall in RAG?**
   Precision is the share of retrieved chunks that are relevant; recall is the
   share of relevant chunks that were retrieved. They trade off through ``k`` and
   the chunking strategy (see :ref:`rag_retrieval_quality`).

**How would you improve a RAG system whose answers are poor?**
   First determine whether retrieval or generation is at fault by checking
   whether the answer is in the retrieved chunks. If not, improve retrieval:
   hybrid search, reranking, query rewriting, or better chunking. If yes, improve
   the prompt or the model.

Frameworks
----------

**What does LangChain provide, and what does LangGraph add?**
   LangChain provides interchangeable components and the ``Runnable`` interface.
   LangGraph adds explicit state, nodes, and edges for workflows that branch or
   loop (see :ref:`rag_frameworks`).

**Why does RAGdoll use LangGraph if its workflow is linear?**
   Explicit state, room for branching such as a relevance check or a retry loop,
   and testable nodes. The trade-off is a little framework overhead.

Concurrency and production
--------------------------

**What would you change to serve many concurrent users?**
   Persistent shared vector storage, a bounded and monitored LLM client with
   timeouts and retries, a caching layer, and horizontal scaling behind a load
   balancer. See :ref:`concurrency_and_scalability` for the detail.

**Why is an in-memory vector store a problem for several instances?**
   Each process builds its own copy at start-up, so memory use multiplies with
   the number of instances, re-indexing requires restarting every process, and
   instances can serve different content if their documents diverge.
