.. _rag_vector_stores:

Vector stores
=============

A vector store holds the embedded chunks and answers one question efficiently:
*which stored vectors are closest to this query vector?* Retrieval depends on
that operation, so this page covers what a vector store does, how similarity
search and top-k retrieval work, how metadata filtering narrows results, and
why production systems use approximate search.

What a vector database does
---------------------------

A vector database stores three things for each item:

* the **vector**, the embedding of the chunk;
* the **payload**, the original text, which is what the LLM eventually reads;
* the **metadata**, such as the source file and its relative path.

It also builds an index over the vectors so that similarity queries do not have
to compare the query with every stored vector. It may also provide persistence,
concurrent access, deletion and updates, and filtering.

RAGdoll's store is much simpler. It is an in-memory store, a Python object that
keeps the vectors and documents in process memory. Its contents are lost on
restart, and it is not shared between processes. The factory is:

.. literalinclude:: ../../../app/infrastructure/vector_store.py
   :pyobject: create_in_memory_vector_store
   :language: python

The knowledge base is built at start-up by
:func:`~app.services.knowledge_base.build_knowledge_base`, which creates an empty
store and then adds the chunks with ``index_documents``. Each chunk is embedded
once, when it is added.

Similarity search
-----------------

Similarity search takes a query, embeds it with the same model, and returns the
stored items with the highest similarity. The steps are:

1. Embed the question with ``embed_query``.
2. Compute the similarity between the query vector and every stored vector.
3. Sort the scores in descending order.
4. Return the top results together with their payloads and metadata.

``InMemoryVectorStore`` performs an exhaustive search. It computes cosine
similarity against every stored vector. This is exact, and for a few hundred
chunks it is very fast. The cost grows linearly with the number of stored
chunks, which is why the approach stops scaling for large collections (see
:ref:`approximate_nearest_neighbour`).

Top-k retrieval
---------------

The top-k parameter sets how many results are returned. RAGdoll's retriever is
created with the store's default of ``k=4``, so each question sends four chunks
to the LLM. The retrieval node calls the retriever through LangChain's standard
interface:

.. literalinclude:: ../../../app/rag/retrieval.py
   :pyobject: create_retrieval_node
   :language: python

The choice of ``k`` is a trade-off:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Smaller ``k``
     - Larger ``k``
     - Effect
   * - Less context to pay for
     - More context to pay for
     - Cost and latency scale with the number of tokens sent.
   * - Higher precision, risk of missing an answer
     - Higher recall, risk of noise
     - More chunks increase the chance of including the answer but also of
       including irrelevant text that distracts the LLM.
   * - Less room for an answer split across chunks
     - More room, within the context window
     - Answers that span several chunks need a higher ``k``.

Metadata filtering
------------------

Metadata filtering restricts the search to items whose metadata matches a
condition, for example ``source == "-pre.md"``. Filtering is applied before or
during the similarity search, depending on the store. It is useful when the user
or the application knows the scope of the question, such as a product version,
a language, or a document set.

RAGdoll does not filter. The retriever searches the whole knowledge base, and
the metadata is returned only so that answers can cite their sources (see
:ref:`rag_document_processing`). Filtering is a natural extension, because the
metadata is already stored with each chunk. The ``search_kwargs`` parameter of
the retriever is the place where a filter would be passed.

.. _approximate_nearest_neighbour:

Approximate nearest-neighbour search
------------------------------------

Exact search becomes expensive when there are millions of vectors. *Approximate
nearest-neighbour* (ANN) search trades a small loss of accuracy for a large gain
in speed. At a conceptual level, ANN indexes organise the vectors so that a
query only examines a small part of the collection.

Common families of index are:

* **Graph-based indexes**, such as HNSW (Hierarchical Navigable Small World).
  They connect each vector to a set of nearby vectors and walk the graph
  towards the query. Malkov and Yashunin describe the method in
  https://arxiv.org/abs/1603.09320.
* **Partition-based indexes**, such as IVF (inverted file). They cluster the
  vectors and search only the clusters closest to the query. FAISS implements
  these and related methods; see https://arxiv.org/abs/1702.08734.
* **Compressed representations**, such as product quantisation. They store
  smaller approximations of the vectors to save memory.

ANN introduces a *recall* parameter: the fraction of the true nearest neighbours
that the index actually returns. Tuning the index trades recall against latency
and memory. For the size of RAGdoll's knowledge base, exhaustive search is
exact and fast enough, so no index is needed.

Choosing a vector store
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Option
     - Typical use
     - Trade-offs
   * - In-memory (RAGdoll today)
     - Small, read-mostly collections in one process
     - No persistence, no sharing between instances, memory bound by one process.
   * - Local embedded database (for example Chroma, or FAISS saved to disk)
     - Prototypes and single-machine applications
     - Persistent, simple, but usually limited to one writer and one host.
   * - Server database (for example PostgreSQL with pgvector, Qdrant, Weaviate,
       Milvus)
     - Multi-user and production systems
     - Shared, persistent, filterable, and scalable, but an extra service to run
       and operate.

Chroma is listed as a planned option in the project README. It is not a
dependency of RAGdoll today.

Further reading
---------------

* LangChain vector stores and retrievers:
  https://python.langchain.com/docs/concepts/vectorstores/
* Malkov and Yashunin, *Efficient and robust approximate nearest neighbor search
  using Hierarchical Navigable Small World graphs* (2016):
  https://arxiv.org/abs/1603.09320
* Johnson, Douze and Jégou, *Billion-scale similarity search with GPUs* (2017),
  the FAISS paper: https://arxiv.org/abs/1702.08734
