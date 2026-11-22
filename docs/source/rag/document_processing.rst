.. _rag_document_processing:

Document processing
===================

Before anything can be retrieved, the source documents must be loaded, split
into chunks, and annotated with metadata. These steps run once when the
knowledge base is built.

Document loading
----------------

A *loader* reads raw content from a source (files, a database, a web page) and
returns a list of *documents*. In LangChain a document is an object with two
attributes: ``page_content`` (the text) and ``metadata`` (a dictionary of
descriptive values).

RAGdoll's loader is a plain function. It searches the configured directory
recursively, keeps files with a ``.md`` suffix, skips empty files, and returns
one document per file:

.. literalinclude:: ../../../app/infrastructure/document_loader.py
   :pyobject: load_markdown_documents
   :language: python

Two design choices are worth noting. First, the results are sorted, so the
index is built in the same order on every run. Second, a file that is not valid
UTF-8 raises :class:`~app.infrastructure.document_loader.DocumentLoadError`
rather than being silently skipped or partially decoded. The error is then
converted into a :class:`~app.services.knowledge_base.KnowledgeBaseError`, so
that a broken document set cannot produce a partially built index.

Text splitting and chunking
---------------------------

A whole document is usually too large to be useful as a retrieval unit, for
three reasons.

* **Embedding models have input limits.** A model converts a fixed number of
  tokens into one vector. Text beyond that limit is truncated or rejected. For
  example, the default embedding model used by RAGdoll
  (``sentence-transformers/all-MiniLM-L6-v2``) has a maximum sequence length of
  256 word pieces, which is shorter than many documents.
* **A single vector summarises the whole input.** A vector for a 20-page
  document represents its average topic. A vector for a paragraph can match a
  specific question much more precisely. This improves *precision*.
* **The LLM has a limited budget.** Retrieved text must fit into the prompt
  together with the instructions and the question. Passing four short passages
  is cheaper and clearer than passing four full documents.

*Chunking* divides documents into smaller pieces. Common strategies are:

* **Fixed-size character or token windows.** Simple and predictable, but they
  can cut sentences and code blocks in the middle.
* **Recursive, separator-based splitting.** Try to split at the largest natural
  boundary first (paragraphs, then lines, then words), and only fall back to
  smaller separators when a piece is still too long. This is the strategy used
  by RAGdoll.
* **Structure-aware splitting.** Use headings, sections, or the document
  hierarchy (for example Markdown headings) as boundaries.
* **Semantic splitting.** Start a new chunk where the embedding of consecutive
  sentences changes sharply. This is more expensive and harder to explain, so it
  is seldom the first choice.

RAGdoll uses ``RecursiveCharacterTextSplitter`` from LangChain. Its default
separators are ``"\n\n"``, ``"\n"``, ``" "``, and ``""``, and the chunk length
is measured in characters. The function that performs the split is:

.. literalinclude:: ../../../app/rag/chunking.py
   :pyobject: split_documents
   :language: python

.. _rag_chunk_size_overlap:

Chunk size and overlap
^^^^^^^^^^^^^^^^^^^^^^

Two settings control the splitting. Their values are defined in
:class:`~app.core.config.Settings` and can be changed through ``CHUNK_SIZE`` and
``CHUNK_OVERLAP``.

* ``chunk_size`` is the maximum number of characters per chunk. The default is
  ``1000``.
* ``chunk_overlap`` is the number of characters that adjacent chunks share. The
  default is ``200``.

Overlap exists because an answer is often spread across a boundary. If a
sentence that defines an option is split between two chunks, neither chunk may
match the question well. Repeating the last characters of one chunk at the
start of the next keeps such sentences intact in at least one chunk.

The choice of size is a trade-off:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Smaller chunks
     - Larger chunks
     - Effect
   * - Each vector is more focused.
     - Each vector covers more topics.
     - Precision versus recall of retrieval.
   * - Many chunks, so more index entries and more search work.
     - Fewer chunks, so less storage and fewer comparisons.
     - Index size and cost.
   * - A question may need several chunks to be answered.
     - A single chunk can hold the whole explanation.
     - Completeness of each retrieved passage.
   * - Less text per source, so less context is used.
     - More text per source, so more context is used.
     - Prompt length and cost.
   * - Greater risk that a sentence is cut at a bad point.
     - Less overlap is needed to avoid cuts.
     - Boundary effects.

The constraints are enforced by ``split_documents``: the size must be positive,
and the overlap must be non-negative and smaller than the size. Violations raise
``ValueError``, which the knowledge-base builder converts into a
``KnowledgeBaseError``.

With the default settings, the nine GetDP Markdown files in ``data/documents/``
(including the dataset's ``README.md``) produce 37 chunks, between 194 and 998
characters long. The overlap of 200 characters is 20% of the chunk size, a
common starting point. The right values depend on the documents and on the
questions, and should be checked with evaluation rather than assumed.

Metadata
--------

*Metadata* is information about a document that is not part of its text, such as
its file name, its location, its author, or its date. It is stored with each
vector and returned with each retrieved chunk. Metadata serves three purposes.

1. **Provenance and citations.** The application can show the user where an
   answer came from.
2. **Filtering.** Vector stores can restrict a search to documents that match
   metadata conditions, for example only documents of one product version.
   RAGdoll does not use filtering yet (see :ref:`rag_vector_stores`).
3. **Debugging.** Metadata makes it possible to see which file produced a poor
   answer.

``split_documents`` gives every chunk a copy of its parent's metadata, so each
chunk remains traceable to its file. The loader sets two keys for every file:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Value
   * - ``source``
     - The file name, for example ``command_line.md``.
   * - ``relative_path``
     - The path relative to ``DOCUMENTS_DIR``, using forward slashes, for example
       ``guides/install.md``. It distinguishes files that have the same name in
       different folders.

A chunk from the GetDP dataset therefore carries metadata similar to this:

.. code-block:: python

   {"source": "command_line.md", "relative_path": "command_line.md"}

The API returns this metadata with each source. The ``section`` field of
:class:`~app.api.schemas.SourceDocument` is read from a ``section`` metadata key,
but the current loader does not set that key, so the field is ``null`` for all
sources. Adding section headings to the metadata would be a natural extension.

Common pitfalls
---------------

* **Losing structure.** Splitting by characters can separate a heading from the
  text it introduces. Include the heading in each chunk, or store it as
  metadata, to keep the chunk meaningful.
* **Duplicating or dropping text.** Overlap duplicates text by design. A
  chunk that is too short can be unhelpful. The splitter does not merge chunks
  across documents, so a short final chunk stays as it is (the shortest GetDP
  chunk is 194 characters).
* **Mixing content types.** Code samples, tables, and prose need different
  handling. A character splitter can break a table row or a code block.
