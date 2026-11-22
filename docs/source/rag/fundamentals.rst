.. _rag_fundamentals:

Fundamentals
============

Traditional LLM inference
-------------------------

A large language model is a neural network with billions of parameters. Given a
sequence of tokens (roughly, word pieces), it predicts a probability
distribution over the next token. Generation repeats this step, appending each
chosen token to the input, until the answer is complete.

When you call a model through an API such as OpenAI or Ollama, the process is
roughly:

1. The application sends a prompt: instructions, conversation history, and the
   user's question.
2. The model computes a response using only the parameters learned during
   training and the tokens in the prompt.
3. The response is returned as text. The model has no built-in way to look up
   a document, check a fact, or cite a source.

Two properties follow from this design and shape everything in RAG.

**Knowledge is fixed at training time.** Facts the model learned are stored
implicitly in its weights. They are only as recent as the training data, which
has a *knowledge cut-off*. Questions about later events, or about documents
that were never in the training corpus (for example an internal manual), can
only be answered if the model happens to know them.

**The context window is finite.** The prompt, including any supplied text, must
fit into a fixed number of tokens. Anything outside the window is invisible to
the model for that request.

Hallucinations
--------------

A *hallucination* is a fluent answer that is not supported by any reliable
source. LLMs are trained to produce plausible continuations, not to report when
they lack knowledge. When a question is about something the model does not
know, it may still generate a confident answer, often with invented names,
numbers, or citations.

Hallucinations matter most when the user cannot easily check the answer. For
technical documentation, a plausible but wrong command-line option is a common
failure mode.

How RAG addresses these problems
--------------------------------

*Retrieval-augmented generation* combines two steps:

1. **Retrieval.** Find the passages in an external document collection that are
   most relevant to the question.
2. **Generation.** Give those passages to the LLM as context, with instructions
   to answer from them, and return the answer.

RAG does not make the model know more. It changes what the model is asked to
do: instead of recalling an answer, it reads supplied text and summarises it.
This addresses the problems above in the following ways.

* **Freshness and private knowledge.** Updating the answers means updating the
  documents and rebuilding the index, not retraining the model.
* **Grounding.** The prompt tells the model to answer only from the context.
  RAGdoll's instructions say to state explicitly when the context does not
  contain enough information (see :ref:`rag_generation`).
* **Traceability.** Because the retrieved passages are known to the system, they
  can be returned as sources and checked by the user.

RAG does not eliminate hallucinations. The model can still misread the context,
combine passages incorrectly, or ignore the instructions. Retrieval can also
fail, so the right passage is never supplied. These are the reasons for the
quality measures in :ref:`rag_retrieval_quality`.

Training, fine-tuning, and retrieval augmentation
-------------------------------------------------

There are three main ways to adapt an LLM to a specific domain. They differ in
what is changed and where the new knowledge lives.

.. list-table::
   :header-rows: 1
   :widths: 20 26 27 27

   * -
     - Pre-training
     - Fine-tuning
     - Retrieval augmentation (RAG)
   * - What changes
     - All model weights, from a very large general corpus.
     - Some or all weights, using a smaller labelled or task-specific dataset.
     - Nothing in the model. The prompt is extended with retrieved text.
   * - Where knowledge lives
     - Implicitly, in the weights.
     - Implicitly, in the weights.
     - Explicitly, in the document store.
   * - Cost
     - Very high (large compute, data curation).
     - Moderate to high (training runs, evaluation, serving a custom model).
     - Low to moderate (embedding and indexing, plus longer prompts).
   * - Time to update facts
     - Retraining.
     - Another fine-tuning run.
     - Edit the documents and re-index.
   * - Traceability of answers
     - Not available.
     - Not available.
     - Sources can be returned with each answer.
   * - Best suited to
     - Building a general model.
     - Changing style, format, or task behaviour.
     - Answering questions over a changing body of documents.

Fine-tuning mainly teaches the model *how* to behave, such as a response style
or a structured output format. It is a poor way to teach it a large, changing
set of facts. RAG is usually the better fit for knowledge; the two techniques
can also be combined.

Example from RAGdoll
--------------------

Consider the question *"Which option runs only the pre-processing stage of
GetDP?"* A model without retrieval might guess an option name. In RAGdoll the
question is embedded, the most similar chunks are retrieved from the GetDP
summaries, and the chunk from ``command_line.md`` that describes ``-pre`` is
passed to the model together with the question. The answer can then be checked
against the returned ``source``.

Further reading
---------------

* Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP
  Tasks* (2020): https://arxiv.org/abs/2005.11401
* Ji et al., *Survey of Hallucination in Natural Language Generation* (2023):
  https://arxiv.org/abs/2202.03629
