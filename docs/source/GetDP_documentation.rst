.. _getdp_documentation:

GetDP documentation as the knowledge base
=========================================

RAGdoll needs a document collection to answer questions about. It uses the
documentation of **GetDP**, a finite element solver, as its example knowledge
base. This page explains what GetDP is, why technical scientific documentation
is a good test for RAG, what the bundled Markdown files contain, and how they
move through the pipeline described in :ref:`RAG_background`.

.. warning::

   The Markdown files in ``data/documents/`` are *condensed summaries*. They
   are not the GetDP manual, and they do not cover all of it. The official
   manual is the authoritative source. The distinction is explained in
   :ref:`getdp_original_vs_condensed`.

What GetDP is
-------------

GetDP (*General environment for the treatment of Discrete Problems*) is an
open-source finite element solver. According to its project site, it uses
conforming finite elements (nodal, edge, face and volume) to discretise de Rham
complexes in one, two and three dimensions. It was designed for
electromagnetic problems and has grown into a general-purpose solver for
multiphysics problems, optionally coupled with lumped circuit elements.

Its defining feature is the close correspondence between a problem's
mathematical formulation and its text description. A problem is written in an
ASCII ``.pro`` file as a set of named objects, and GetDP runs it in stages:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Stage
     - Purpose
   * - ``-pre``
     - Pre-processing: read the problem definition and the mesh.
   * - ``-cal``
     - Processing: assemble and solve the discrete problem.
   * - ``-pos``
     - Post-processing: compute and export derived quantities.
   * - ``-solve``
     - Combined run of the resolution, used in the examples.

Official references:

* Project website: https://www.getdp.info/
* Reference manual, in HTML, PDF and plain text: https://getdp.info/doc/texinfo/getdp.txt
* Source code: https://github.com/getdp/getdp
* Tutorials and examples are listed on the project site.

Why technical documentation makes a good RAG test set
-----------------------------------------------------

Technical documentation is a useful test dataset for RAG for several reasons.

* **Answers are factual and checkable.** A question such as *"which stage
  writes the post-processing results?"* has a single correct answer that can be
  compared with the source.
* **Precise terms matter.** Option names such as ``-pre`` and object names such
  as ``FunctionSpace`` must be retrieved exactly. This exposes the limits of
  embeddings, which can miss rare identifiers (see :ref:`rag_retrieval_quality`).
* **Structure matters.** Reference material is organised into sections, and a
  good chunker keeps a definition together with its context.
* **Unanswerable questions are easy to design.** Asking about a feature the
  dataset does not describe tests whether the system declines to guess, which
  is the grounding behaviour described in :ref:`rag_generation`.

What the dataset can answer
---------------------------

The bundled files cover the solver's purpose, installation, the file formats,
the command-line stages, the main problem-definition objects, a tutorial
catalogue, and some troubleshooting. Typical questions include:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Question type
     - Example
   * - Definition
     - What is GetDP, and which kinds of problems does it solve?
   * - Procedure
     - How do I run only the pre-processing stage?
   * - Reference
     - Which objects make up a ``.pro`` problem definition?
   * - File formats
     - Which format does GetDP expect for a mesh, and what is the ``.pro`` file?
   * - Troubleshooting
     - What should I check if GetDP cannot read my mesh?
   * - Out of scope
     - Questions about GetDP versions, options, or tutorials that the summaries
       omit should be declined rather than answered from memory.

Structure of the document collection
------------------------------------

The collection is a flat directory of nine Markdown files. Eight are summaries
of topics from the manual, and one is a README that describes the collection.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Content
   * - ``README.md``
     - Describes the collection and its source.
   * - ``overview.md``
     - Purpose, capabilities, and main concepts of GetDP.
   * - ``installation.md``
     - Obtaining binaries and building from source.
   * - ``data_formats.md``
     - The ``.pro``, ``.msh``, ``.pre``, and ``.res`` formats and exported results.
   * - ``command_line.md``
     - Execution stages and command-line options.
   * - ``problem_definition.md``
     - The main objects used to define a model.
   * - ``tutorials_and_examples.md``
     - Tutorial catalogue and example workflows.
   * - ``troubleshooting.md``
     - Frequently asked questions and common problems.
   * - ``source_and_attribution.md``
     - Source, licence, version, and suggested citation.

Each file uses Markdown headings (``#`` and ``##``). These headings are useful
for humans, but RAGdoll's splitter does not use them to define chunk boundaries,
as explained below.

.. _getdp_original_vs_condensed:

Original documentation and condensed summaries
----------------------------------------------

The two must be kept distinct.

.. list-table::
   :header-rows: 1
   :widths: 25 37 38

   * - Aspect
     - Official GetDP manual
     - RAGdoll Markdown collection
   * - Scope
     - The full reference manual and the tutorials.
     - Selected topics, summarised.
   * - Authority
     - Authoritative for its version.
     - Not authoritative. It may omit or simplify details.
   * - Version
     - Reference Manual 4.0.0, dated November 16, 2026, according to the dataset.
     - Based on that manual, and sensitive to the same version.
   * - Licence
     - Governed by the GetDP licence and the manual's copyright notice.
     - Independently written notes, attributed in ``source_and_attribution.md``.

The attribution file also contains the notice and the suggested citation for
GetDP. Readers who want the complete and current information should consult the
official manual.

How the documents are processed
-------------------------------

The documents move through the pipeline described in :ref:`RAG_background`.
The sizes below are from the bundled dataset at the default settings
(``CHUNK_SIZE=1000`` and ``CHUNK_OVERLAP=200``).

**Loading.** The loader reads every Markdown file in the configured directory
and returns one LangChain ``Document`` per file, with the file's text as its
content and its name and path as metadata. The code is described in
:ref:`rag_document_processing`.

.. literalinclude:: ../../app/infrastructure/document_loader.py
   :pyobject: load_markdown_documents
   :language: python

**Chunking.** Each document is split with ``RecursiveCharacterTextSplitter``,
which tries to split on paragraph breaks first, then line breaks, then spaces.
The nine documents become 37 chunks, between about 200 and 1000 characters
each. The splitter works on each document separately, so a chunk never spans
two files.

**Indexing.** Each chunk is embedded with the local model and added to the
in-memory vector store (see :ref:`rag_embeddings` and :ref:`rag_vector_stores`).

**Retrieval.** A question is embedded in the same way, and the four most similar
chunks are returned.

**Generation.** The chunks are placed in the prompt, and the model answers
from them (see :ref:`rag_generation`).

Preservation of source metadata
-------------------------------

Each chunk keeps the metadata of the document it came from. In RAGdoll this is
the file name in ``source`` and the path relative to the documents directory in
``relative_path``. Splitting copies the metadata to every chunk, so the response
can cite the file that supplied each passage.

The API response also has a ``section`` field. The route layer reads
``section`` from the metadata, but the loader does not set it, so ``section`` is
currently ``null`` for every source. A section-aware loader that records the
heading of each chunk is a natural improvement and is discussed in
:ref:`rag_retrieval_quality`.

Scope and limitations
---------------------

* The dataset is a sample, not the GetDP manual, and it is small enough to
  search exhaustively in memory.
* Chunks are cut by characters, not by Markdown headings. A chunk can therefore
  begin in the middle of a section.
* The summaries are versioned. Answers about another GetDP version may be wrong.
* Retrieval of exact option names depends on the embedding model and may miss
  them. Evaluation should include such questions.

Further reading
---------------

* GetDP project site: https://www.getdp.info/
* GetDP reference manual: https://getdp.info/doc/texinfo/getdp.txt
* GetDP source code: https://github.com/getdp/getdp
