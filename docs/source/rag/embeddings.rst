.. _rag_embeddings:

Embeddings
==========

Retrieval needs a way to decide that *"how do I run only the pre-processing
step?"* is related to a passage that describes ``-pre``, even though the two
share few words. Embeddings provide that measure of meaning.

What an embedding represents
----------------------------

An *embedding* is a fixed-length list of real numbers, a **vector**, that
represents a piece of text. A model maps a sentence or a passage to a point in a
high-dimensional space so that texts with similar meaning are placed close to
each other and unrelated texts are placed far apart.

The default model used by RAGdoll, ``sentence-transformers/all-MiniLM-L6-v2``,
produces vectors with **384 dimensions** for any input. A short question and a
long passage therefore both become 384 numbers, which makes them directly
comparable.

How embedding models work
-------------------------

Embedding models are neural networks, usually transformer encoders, that
convert text into vectors. Conceptually, the process has four steps:

1. **Tokenisation.** The text is split into tokens (word pieces) and each token
   is mapped to an integer identifier.
2. **Contextual encoding.** Transformer layers compute a representation for each
   token that depends on the surrounding tokens. The word *"bank"* therefore gets
   different representations in *"river bank"* and *"bank account"*.
3. **Pooling.** The token representations are combined into a single vector,
   commonly by averaging them (mean pooling).
4. **Normalisation (optional).** The vector may be scaled to unit length.

Such models are trained so that the vectors of related texts, for example a
question and the passage that answers it, are close, while the vectors of
unrelated texts are pushed apart. This is often done with *contrastive* training
on large collections of text pairs.

RAGdoll uses a **bi-encoder** arrangement. The question and each chunk are
encoded *separately*, and their vectors are compared. This is what makes it
practical to pre-compute one vector per chunk and search them quickly. A
*cross-encoder* instead reads the question and a chunk together, which is more
accurate for ranking a small set of candidates but far too slow to run against
every chunk in a collection. Cross-encoders are a common reranking step (see
:ref:`rag_retrieval_quality`).

Vector representations and semantic similarity
----------------------------------------------

Semantic similarity means that two texts are close in meaning, even when their
wording differs. Embeddings capture this, to a degree, which gives RAG its main
advantage over keyword search. A question such as *"How can I see the
results?"* can retrieve a passage about post-processing and visualisation, even
though the words "see" and "results" do not appear in it.

Embeddings are approximate. They are trained on general text, so they can
miss exact identifiers. GetDP option names such as ``-pre``, ``-cal``, and
``-pos`` are short and rare, and a question that depends on an exact string
may retrieve a passage that is semantically close but not the one that names
the option. This is one motivation for hybrid search (see
:ref:`rag_retrieval_quality`).

Similarity measures
-------------------

Once the question and the chunks are vectors, a *similarity measure* gives a
score for each pair. The most common measures are listed below, where
:math:`\mathbf{a}` and :math:`\mathbf{b}` are two vectors.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Measure
     - Formula
     - Notes
   * - Cosine similarity
     - :math:`\cos(\mathbf{a},\mathbf{b}) = \dfrac{\mathbf{a}\cdot\mathbf{b}}{\lVert\mathbf{a}\rVert\,\lVert\mathbf{b}\rVert}`
     - Measures the angle between vectors and ignores their length. Values
       range from -1 to 1; higher means more similar. The most common choice
       for text.
   * - Dot product
     - :math:`\mathbf{a}\cdot\mathbf{b} = \sum_i a_i b_i`
     - Depends on length as well as direction. For unit-length vectors it equals
       cosine similarity.
   * - Euclidean distance
     - :math:`\lVert\mathbf{a}-\mathbf{b}\rVert_2`
     - A distance, so smaller means more similar. It is sensitive to vector
       length, and for unit-length vectors it ranks results in the same order as
       cosine similarity.

Cosine similarity is the usual choice for text embeddings because the length of
a vector often reflects properties of the text, such as its length, rather than
its meaning. RAGdoll's :class:`~langchain_core.vectorstores.InMemoryVectorStore`
computes cosine similarity for every query, so the ranking does not depend on
whether the embedding model normalises its output. RAGdoll's factory does not
set ``normalize_embeddings``, so the ``langchain-huggingface`` default applies.

Compatibility of the embedding model
------------------------------------

The vectors in the index and the vector of a question must come from the **same
embedding model**, with the same tokenisation, the same preprocessing, and the
same version. Two models produce spaces with different dimensions and different
geometry, so comparing their vectors gives meaningless scores. Even two models
with the same dimension are not interchangeable.

In practice this means:

* Changing ``EMBEDDING_MODEL`` requires rebuilding the entire index. Old vectors
  must not be searched with a new model.
* A persistent index must record which model produced it, so a mismatch can be
  detected.
* Upgrading a library that changes the model's preprocessing can silently
  degrade retrieval.

RAGdoll avoids the most common form of this error by construction. The same
``Embeddings`` object is passed to the vector store, which calls
``embed_documents`` when chunks are added and ``embed_query`` when a question is
searched. The wiring is in :func:`~app.services.knowledge_base.build_knowledge_base`
and :func:`~app.api.dependencies.get_question_service`.

The embedding model in RAGdoll
------------------------------

RAGdoll runs the embedding model locally with Sentence Transformers, through the
``langchain-huggingface`` integration. The factory is small:

.. literalinclude:: ../../../app/infrastructure/embeddings.py
   :pyobject: create_embeddings
   :language: python

The trade-offs of a local model are as follows.

* **No API key and no per-call cost.** Embedding runs on the same machine as the
  application.
* **A one-time download.** The weights are fetched from Hugging Face on first
  use, which is part of the first question's latency.
* **CPU or GPU load.** Embedding every chunk at start-up, and every question at
  query time, consumes compute in the application process.
* **Input truncation.** ``all-MiniLM-L6-v2`` uses at most 256 word pieces per
  input and silently ignores the rest. A chunk of 1000 characters usually fits,
  but the end of a long chunk is not represented in its vector. Smaller chunks
  avoid this (see :ref:`rag_chunk_size_overlap`).

Hosted embedding APIs remove the local compute cost but add latency, a
dependency on a provider, and data-sharing considerations. The configuration
hooks in :class:`~app.core.config.Settings` make the model replaceable, but
switching providers would also require re-indexing.

Further reading
---------------

* Reimers and Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese
  BERT-Networks* (2019): https://arxiv.org/abs/1908.10084
* Sentence Transformers documentation: https://www.sbert.net/
* The model card for ``sentence-transformers/all-MiniLM-L6-v2``:
  https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
