.. _rag_retrieval_quality:

Retrieval quality
=================

A RAG answer can only be as good as the context it receives. If the right chunk
is not retrieved, the LLM cannot use it. This page explains how retrieval is
measured, the trade-offs in chunking, and the common ways to improve results.
It also says which of these RAGdoll implements today.

Measuring retrieval
-------------------

Retrieval is a search problem, so it is measured with the standard information
retrieval metrics. Each question needs a set of chunks labelled as relevant
for it, which is a *gold* or *reference* set.

**Precision** is the fraction of retrieved chunks that are relevant:

.. math::

   \text{precision@}k = \frac{\text{relevant chunks in the top } k}{k}

**Recall** is the fraction of all relevant chunks that were retrieved:

.. math::

   \text{recall@}k = \frac{\text{relevant chunks in the top } k}{\text{all relevant chunks}}

The two pull in opposite directions. Increasing ``k`` usually raises recall and
lowers precision. Ranking metrics such as *mean reciprocal rank* (MRR) and
*normalised discounted cumulative gain* (nDCG) also consider the position of the
relevant chunks, which matters because the LLM reads the context in order.

For RAG, the most useful question is often simpler: *does the top-k set contain
the passage that answers the question?* This is called **hit rate**, and it can
be measured on a small set of hand-written questions.

Retrieval relevance
-------------------

Relevance is the judgement that a chunk helps answer the question. It is not the
same as similarity. A chunk can be semantically similar but not useful, such as
a passage that describes an option in general without saying what it does. The
reverse also happens: an answer may be in a chunk that shares few words with the
question.

The embedding score measures similarity only. Relevance is therefore best
evaluated against questions with known answers, which is the approach described
in :ref:`rag_faq`.

Chunking trade-offs
-------------------

Chunking affects retrieval directly, through the balance between two opposing
effects:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Chunk size
     - Small chunks
     - Large chunks
   * - Precision
     - Each chunk is focused, so a match is likely relevant.
     - A chunk may mix several topics, and the embedding averages them.
   * - Context
     - An answer may be split across chunks and missed.
     - An answer is more likely to stay in one piece.
   * - Cost
     - More chunks to index and store.
     - Fewer chunks, but more tokens sent per chunk.
   * - Embedding fidelity
     - Each vector represents a narrow idea.
     - Long chunks can exceed the model's input limit (see :ref:`rag_embeddings`).

Overlap reduces the risk of splitting an answer, at the cost of duplicated text
and extra index entries. The defaults in RAGdoll (1000 characters with 200
overlap) are a reasonable starting point, not an optimum. They should be tuned
against the question set (see :ref:`rag_chunk_size_overlap`).

Improvements
------------

The following techniques are common in production RAG systems. Each addresses a
specific failure.

Hybrid search
^^^^^^^^^^^^^

Hybrid search combines dense retrieval (embeddings) with sparse retrieval such as
BM25, a keyword-scoring method. Keyword search is exact on rare terms and
identifiers, such as option names like ``-pre``, while embeddings handle
paraphrase. The two ranked lists are merged, for example with *reciprocal rank
fusion*.

Reranking
^^^^^^^^^

A reranker takes the top candidates, often 20 to 50, and rescores them with a
model that reads the question and each chunk together, usually a cross-encoder.
Reranking is slower than vector search but much more accurate on a small list.
It is the standard way to improve precision without changing the index.

Query rewriting
^^^^^^^^^^^^^^^

Users often write short or vague questions. Query rewriting uses an LLM to turn
the question into one or more better search queries, for example by expanding
abbreviations, resolving pronouns in a conversation, or splitting a compound
question into parts whose results are then merged.

Better chunking
^^^^^^^^^^^^^^^

Splitting along the document's structure, such as headings or sections, keeps
related text together. Sentence- or section-aware chunkers, and storing a
parent section alongside each small chunk, both improve context without
sacrificing precision.

Metadata filters
^^^^^^^^^^^^^^^^

Filtering by metadata restricts the search to the relevant subset, such as a
product version or document type. This improves precision when the scope of a
question is known (see :ref:`rag_vector_stores`).

RAGdoll today
-------------

RAGdoll implements a single dense retrieval step. It uses a default ``k=4``, a
cosine-similarity search over the chunks, and no reranking, no hybrid search,
no query rewriting, and no metadata filtering. The design is deliberately
simple so that the baseline is easy to understand and measure. The techniques
above are the next steps to try if evaluation shows that retrieval is the
bottleneck.

Further reading
---------------

* Manning, Raghavan and Schütze, *Introduction to Information Retrieval*
  (Cambridge University Press, 2008), chapters on evaluation:
  https://nlp.stanford.edu/IR-book/
* Cormack, Clarke and Büttcher, *Reciprocal Rank Fusion outperforms Condorcet
  and individual Rank Learning Methods* (2009).
* Nogueira and Cho, *Passage Re-ranking with BERT* (2019):
  https://arxiv.org/abs/1901.04085
