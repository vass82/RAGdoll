.. _tutorials_index:

Tutorials
=========

These tutorials take you from an empty machine to a running RAGdoll API that
answers questions about the example GetDP documents. Each tutorial assumes
basic Python and command-line knowledge, and none of them assumes previous
experience with RAG.

The examples target **Ubuntu 24.04** and were checked against the repository
on this branch. Windows notes are given where they differ.

Choose a path
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tutorial
     - Use it when
   * - :ref:`tutorial_local_setup`
     - You want to run RAGdoll directly with Python and uv, using an OpenAI
       API key.
   * - :ref:`tutorial_ollama_setup`
     - You want to avoid a paid LLM API and run the chat model locally with
       Ollama.
   * - :ref:`tutorial_docker_setup`
     - You want to run the API in a Docker container with Docker Compose.
   * - :ref:`tutorial_configuration`
     - You need the meaning, default and accepted values of each setting.
   * - :ref:`tutorial_troubleshooting`
     - Something failed and you want to diagnose it.

Read :ref:`tutorial_configuration` before choosing a provider. The local and
Docker tutorials both reference its variables.

.. toctree::
   :maxdepth: 1
   :caption: Tutorials:

   local_setup
   ollama_setup
   docker_setup
   configuration
   troubleshooting
