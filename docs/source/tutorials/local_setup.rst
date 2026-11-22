.. _tutorial_local_setup:

Local setup without Docker
==========================

This tutorial runs RAGdoll directly on your machine with Python and `uv
<https://docs.astral.sh/uv/>`_. It uses an OpenAI API key for the chat model.
To run without a paid API, follow :ref:`tutorial_ollama_setup` after step 5.

Unless a step says otherwise, run every command in this tutorial on your host,
in the project directory ``~/RAGdoll``.

.. _tutorial_local_prerequisites:

1. Prerequisites
----------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Requirement
     - Details
   * - Python 3.12 or newer
     - Required by ``requires-python`` in ``pyproject.toml``. Ubuntu 24.04
       ships Python 3.12. If your Python is older, uv can install one (step 1).
   * - uv
     - Installs Python dependencies from ``uv.lock``. The CI workflow uses
       uv 0.13.7.
   * - Git
     - To clone the repository.
   * - Disk space
     - Several gigabytes. Installing the dependencies pulls in PyTorch with its
       CUDA libraries. The virtual environment was 5.6 GB in our verification.
   * - Network access
     - To PyPI (dependencies) and to ``huggingface.co`` (the embedding model is
       downloaded on first use).
   * - An OpenAI API key
     - Needed for the default provider. Not needed for the tests. For a free
       alternative, see :ref:`tutorial_ollama_setup`.

**Step 1: check Python.** Run:

.. code-block:: bash

   python3 --version

The output must be ``Python 3.12.x`` or later. If it is older, uv installs
Python 3.12 for you during the dependency installation in step 5.

**Step 2: install Git and uv.**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install -y git curl
   curl -LsSf https://astral.sh/uv/install.sh | sh

The uv installer adds uv to ``~/.local/bin``. Load it in the current terminal,
or open a new terminal:

.. code-block:: bash

   source "$HOME/.local/bin/env"
   uv --version
   git --version

Expected: ``uv`` prints a version such as ``uv 0.13.x``, and ``git`` prints a
version number.

.. note::

   **Windows:** use WSL 2 with Ubuntu, and follow this tutorial inside it.
   Native Windows PowerShell instructions are not covered or tested here.

2. Cloning the repository
-------------------------

.. code-block:: bash

   cd ~
   git clone https://github.com/vass82/RAGdoll.git
   cd RAGdoll

The clone creates the directory ``~/RAGdoll``. The clone uses the default
branch. To use a different branch, add ``git switch <branch-name>`` after
``cd RAGdoll``.

3. Entering the project directory
---------------------------------

All remaining commands assume that your current directory is the project root.
Check it with:

.. code-block:: bash

   pwd
   ls

Expected: ``pwd`` prints ``/home/<your-user>/RAGdoll``. The listing includes
``app``, ``data``, ``docs``, ``tests``, ``pyproject.toml`` and ``.env.example``.

The application reads ``.env`` and the document path ``data/documents`` relative
to the current directory. Running the commands from another directory causes
configuration and document errors (see :ref:`troubleshooting_documents_dir`).

4. Creating the ``.env`` configuration file
-------------------------------------------

Copy the example file:

.. code-block:: bash

   cp .env.example .env
   ls -la .env

The ``.env`` file is listed in ``.gitignore``, so it is never committed. Open it
in an editor:

.. code-block:: bash

   nano .env

Set the two lines for the OpenAI provider:

.. code-block:: ini

   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here

Replace ``sk-your-key-here`` with your own key. Leave the other lines as they
are. The defaults are listed in :ref:`tutorial_configuration`.

.. warning::

   ``OPENAI_API_KEY=`` with nothing after the equals sign is treated as a
   missing key. Requests then fail with ``503`` (see
   :ref:`troubleshooting_missing_api_key`).

5. Installing dependencies with uv
----------------------------------

From the project root, run:

.. code-block:: bash

   uv sync --locked

What this does:

* ``uv sync`` creates the virtual environment ``.venv`` in the project and
  installs the packages listed in ``uv.lock``.
* ``--locked`` stops with an error if ``uv.lock`` does not match
  ``pyproject.toml``. This makes the installed versions reproducible.
* The ``dev`` group (pytest, ruff and HTTPX) is installed by default.

The first run downloads several gigabytes. Expected: the command ends without
an error. Check the environment:

.. code-block:: bash

   uv run python -c "import app.main; print('import ok')"

Expected output: ``import ok``.

If uv reports that it cannot find Python 3.12, install it and repeat the sync:

.. code-block:: bash

   uv python install 3.12
   uv sync --locked

6. Configuring the LLM provider
-------------------------------

RAGdoll uses two different models:

* The **chat model** writes the answer. It is served by OpenAI in this
  tutorial. It can also be served by a local Ollama server (see
  :ref:`tutorial_ollama_setup`).
* The **embedding model** converts text into vectors for search. It is
  ``sentence-transformers/all-MiniLM-L6-v2``, which runs on your machine through
  Sentence Transformers. It needs no API key and is not affected by
  ``LLM_PROVIDER``.

For the OpenAI provider, confirm the two values in ``.env``:

.. code-block:: bash

   grep -E '^(LLM_PROVIDER|OPENAI_API_KEY|OPENAI_MODEL)=' .env

Expected: ``LLM_PROVIDER=openai``, a non-empty ``OPENAI_API_KEY``, and
``OPENAI_MODEL=gpt-4o-mini``. The command prints your key, so do not paste the
output into a public place.

7. Starting the application
---------------------------

Start the API server. This terminal stays busy while the server runs:

.. code-block:: bash

   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

Expected output, after a few log lines:

.. code-block:: text

   INFO:     Started server process [12345]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

The application does not load the documents at startup. The knowledge base
(the indexed documents) is built the first time a question is asked. This is
why the first question in step 9 is slow.

Open a **second terminal** for the next steps. Run ``cd ~/RAGdoll`` there too.
Stop the server at any time by pressing ``Ctrl+C`` in the first terminal.

.. note::

   ``.env.example`` also lists ``API_HOST``, ``API_PORT`` and ``APP_ENV``.
   The application does not read them. The host and port come from the
   ``--host`` and ``--port`` options of the command above.

8. Checking the health endpoint
-------------------------------

In the second terminal:

.. code-block:: bash

   curl http://127.0.0.1:8000/health

Expected output:

.. code-block:: json

   {"status":"ok"}

This endpoint only confirms that the API process is running. It does not check
the chat model or the embedding model. A healthy response does not guarantee
that questions will succeed.

9. Sending a question with curl
-------------------------------

.. code-block:: bash

   curl -X POST http://127.0.0.1:8000/api/v1/questions \
     -H "Content-Type: application/json" \
     -d '{"question": "What is GetDP?"}'

Add ``| python3 -m json.tool`` at the end of the command to format the output.

The first question takes longer than later ones. On the first request the
application:

1. Loads the Markdown files from ``data/documents``.
2. Splits them into chunks.
3. Downloads the embedding model from Hugging Face, if it is not cached yet.
4. Converts every chunk into a vector and stores it in memory.

Subsequent requests reuse the stored index. The time depends on your hardware
and network, and it was not measured in our verification.

The request body must be a JSON object with one ``question`` string. The
question is trimmed, must not be empty and can be up to 2000 characters.

10. Understanding the response and source documents
---------------------------------------------------

A successful response has this structure:

.. code-block:: text

   {
     "answer": "<the answer text written by the chat model>",
     "sources": [
       {
         "document_name": "overview.md",
         "section": null,
         "content": "<the text of one retrieved chunk>",
         "metadata": {
           "source": "overview.md",
           "relative_path": "overview.md"
         }
       }
     ]
   }

The placeholders stand for the real text, which depends on the model and the
documents. Run the question yourself to see an actual response.

How to read it:

* ``answer`` is the text generated by the chat model from the retrieved
  chunks. Check it against the sources.
* ``sources`` lists the chunks that were given to the model as context. The
  retriever returns at most four chunks by default.
* ``document_name`` is the file name of the document that the chunk came from.
* ``content`` is the exact chunk text that was retrieved.
* ``metadata`` contains the metadata recorded when the file was loaded:
  ``source`` (the file name) and ``relative_path`` (the path below the
  documents directory, with forward slashes).
* ``section`` is always ``null`` in the current implementation. The loader does
  not record section names. The field is kept for future use.

If no chunk is relevant, ``sources`` is an empty list and the answer is the
fixed text ``I could not find any relevant information in the knowledge base
to answer this question.``. The chat model is not called in that case.

Errors use these HTTP status codes:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Status
     - Meaning
   * - ``422``
     - The request is missing ``question``, or the question is empty or longer
       than 2000 characters.
   * - ``500``
     - An unexpected error occurred. Check the server log.
   * - ``502``
     - The chat model failed, for example the provider is unreachable or the
       API key is rejected.
   * - ``503``
     - The question service could not be initialised, or retrieval failed.
       This includes a missing API key, a missing documents directory and
       a failed embedding model download.

For failures, see :ref:`tutorial_troubleshooting`.

11. Running the automated tests
-------------------------------

The tests do not need an OpenAI key, Ollama or network access. They use fake
models. Run them from the project root:

.. code-block:: bash

   uv run pytest

Expected: the last line reads ``78 passed``, followed by the timing. Run the
same linting and formatting checks as CI:

.. code-block:: bash

   uv run ruff check .
   uv run ruff format --check .

Expected: ``All checks passed!`` from the first command, and
``N files already formatted`` from the second. If you change code, run
``uv run ruff format .`` to apply formatting.

To match CI exactly, add ``--locked`` to each command, for example
``uv run --locked pytest``.

Next steps
----------

* Run the API with a local model: :ref:`tutorial_ollama_setup`.
* Run the API in a container: :ref:`tutorial_docker_setup`.
* Review every setting: :ref:`tutorial_configuration`.
