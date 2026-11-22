.. _tutorial_configuration:

Configuration reference
=======================

RAGdoll reads its settings from environment variables and from a ``.env`` file
in the **current working directory** when the process starts. This page lists
every setting the application reads, as defined in ``app/core/config.py``.

Where the settings come from
----------------------------

* **Local run** (:ref:`tutorial_local_setup`): the ``.env`` file in the project
  root is read because you start the server from that directory.
* **Docker run** (:ref:`tutorial_docker_setup`): the same ``.env`` file is passed
  to the container through ``env_file: .env`` in ``docker-compose.yml``. The
  file itself is not copied into the image.

Environment variables take part in name matching **without regard to case**.
``OPENAI_API_KEY`` and ``openai_api_key`` are the same setting. The
upper-case form is the convention used in ``.env.example``.

Settings that are not defined in ``config.py`` are ignored. See
:ref:`configuration_unused_variables`.

Settings table
--------------

.. list-table::
   :header-rows: 1
   :widths: 20 18 22 14 26

   * - Variable
     - Default
     - Accepted values
     - Mandatory
     - Purpose
   * - ``LLM_PROVIDER``
     - ``openai``
     - ``openai``, ``ollama``
     - No
     - Selects the chat model provider. Any other value is rejected with a
       validation error when the settings are first loaded.
   * - ``OPENAI_API_KEY``
     - not set
     - Your OpenAI API key, for example ``sk-...``
     - Yes, when ``LLM_PROVIDER=openai``
     - Authenticates requests to the OpenAI API. An empty value is treated as
       missing.
   * - ``OPENAI_MODEL``
     - ``gpt-4o-mini``
     - Any chat model name available to your OpenAI account
     - No
     - The OpenAI chat model used to write answers. Used only when
       ``LLM_PROVIDER=openai``.
   * - ``OLLAMA_BASE_URL``
     - ``http://localhost:11434``
     - A URL with scheme, host and port
     - No (required in practice for Docker, see below)
     - Address of the Ollama server. Used only when ``LLM_PROVIDER=ollama``.
   * - ``OLLAMA_MODEL``
     - ``llama3.2``
     - A model name already downloaded in Ollama (``ollama list``)
     - No
     - The Ollama chat model used to write answers. Used only when
       ``LLM_PROVIDER=ollama``.
   * - ``EMBEDDING_MODEL``
     - ``sentence-transformers/all-MiniLM-L6-v2``
     - A Sentence Transformers model name from Hugging Face
     - No
     - The local embedding model that converts documents and questions into
       vectors. Used for both providers. Downloaded on first use.
   * - ``DOCUMENTS_DIR``
     - ``data/documents``
     - A path. Relative paths are resolved from the working directory.
     - No
     - Folder that contains the Markdown documents to index. It must contain at
       least one ``.md`` file.
   * - ``CHUNK_SIZE``
     - ``1000``
     - A positive integer (characters)
     - No
     - Maximum length of each text chunk.
   * - ``CHUNK_OVERLAP``
     - ``200``
     - An integer from ``0`` up to, but not including, ``CHUNK_SIZE``
     - No
     - Number of characters that adjacent chunks share.

.. note::

   The defaults are the values in ``app/core/config.py``. The file
   ``.env.example`` sets the same values, except for ``OPENAI_API_KEY``, which
   is empty in the example.

Mandatory settings
------------------

No setting is mandatory for every configuration. The only requirement is
conditional:

* With ``LLM_PROVIDER=openai`` (the default), ``OPENAI_API_KEY`` must be set to
  a non-empty value. Without it, a question returns HTTP ``503``. See
  :ref:`troubleshooting_missing_api_key`.
* With ``LLM_PROVIDER=ollama``, no API key is needed. Ollama must be running
  and must have the model named in ``OLLAMA_MODEL``.

Validation of the chunking settings
-----------------------------------

``CHUNK_OVERLAP`` must be smaller than ``CHUNK_SIZE``. ``CHUNK_OVERLAP`` must
not be negative, and ``CHUNK_SIZE`` must be positive. Otherwise the
application stops building the knowledge base and reports
``Invalid chunk size or chunk overlap.``

For example, this combination is rejected because the overlap is larger than
the chunk:

.. code-block:: text

   CHUNK_SIZE=500
   CHUNK_OVERLAP=600

OpenAI and Ollama configurations
--------------------------------

Only the chat model changes between the two providers. The embedding model,
the documents and the retrieval steps are the same. The settings for each
provider are:

.. list-table::
   :header-rows: 1
   :widths: 25 37 38

   * - Aspect
     - OpenAI (``LLM_PROVIDER=openai``)
     - Ollama (``LLM_PROVIDER=ollama``)
   * - Chat model
     - Remote, hosted by OpenAI. Set with ``OPENAI_MODEL``.
     - Local, served by an Ollama process you run. Set with ``OLLAMA_MODEL``.
   * - Requires
     - ``OPENAI_API_KEY``, network access to OpenAI, and a billed account.
     - Ollama installed and running, and the model downloaded.
   * - Address setting
     - Not used. The OpenAI endpoint is fixed by the client library.
     - ``OLLAMA_BASE_URL``, which must point to a server that is reachable
       from the process that runs RAGdoll.
   * - Cost
     - Per request, billed by OpenAI.
     - No per-request cost. Uses local CPU or GPU and memory.
   * - Typical first failure
     - ``503`` with no key set (or an empty key).
     - ``502`` when a question reaches the chat model and Ollama is not
       reachable or the model is missing. See
       :ref:`troubleshooting_ollama_not_running`.

The embedding model is the same for both providers and always runs locally
through Sentence Transformers. It is not an OpenAI or Ollama model.

Example configurations
----------------------

OpenAI, run locally:

.. code-block:: text

   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-real-key
   OPENAI_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   DOCUMENTS_DIR=data/documents
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200

Ollama, run locally (Ollama on the same machine):

.. code-block:: text

   LLM_PROVIDER=ollama
   OPENAI_API_KEY=
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2

Ollama, RAGdoll in Docker, Ollama on the Ubuntu host:

.. code-block:: text

   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=llama3.2

This last configuration needs the Compose override and Ollama listening on the
Docker bridge. See :ref:`tutorial_docker_ollama_networking`.

Writing the file
----------------

* One ``NAME=value`` pair per line. Do not put spaces around ``=``.
* Write values without quotes, as in the examples on this page.
* Lines starting with ``#`` are comments.
* Never commit ``.env``. It is listed in ``.gitignore``.

.. _configuration_unused_variables:

Variables in ``.env.example`` that the application does not read
----------------------------------------------------------------

``.env.example`` also contains three variables that are **not read** by any
code in this repository:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Variable
     - Status
   * - ``APP_ENV``
     - Not read by the application. Changing it has no effect.
   * - ``API_HOST``
     - Not read by the application. The host address is set by the command
       that starts uvicorn (``--host``), not by this variable. See
       :ref:`tutorial_local_setup`.
   * - ``API_PORT``
     - Not read by the application. The port is set by the uvicorn command
       (``--port``). The Docker port mapping in ``docker-compose.yml`` is set
       to ``8000:8000``.

They are harmless, because unknown variables are ignored. Do not rely on them
to change the server's address or port.

Next steps
----------

* Start with the provider you chose: :ref:`tutorial_local_setup`,
  :ref:`tutorial_ollama_setup` or :ref:`tutorial_docker_setup`.
* If a setting seems to have no effect, see :ref:`tutorial_troubleshooting`.
