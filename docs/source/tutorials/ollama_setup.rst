.. _tutorial_ollama_setup:

Local Ollama setup
==================

This tutorial runs RAGdoll without a paid LLM API. The chat model runs on your
machine through `Ollama <https://ollama.com>`_. Ollama is a separate program
that downloads, stores and serves open models over a local HTTP API.

Complete :ref:`tutorial_local_setup` steps 1 to 5 first, or follow them as
you go. The steps below replace the OpenAI configuration in step 6 there.

.. contents:: On this page
   :local:
   :depth: 2

Two models, two roles
---------------------

RAGdoll always uses two different models:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Model
     - Role
     - Where it runs with this tutorial
   * - **Chat model**
     - Reads the retrieved chunks and writes the answer.
     - Ollama, using the model named in ``OLLAMA_MODEL`` (default
       ``llama3.2``).
   * - **Embedding model**
     - Turns text into vectors so that chunks can be searched.
     - Inside the RAGdoll process, through Sentence Transformers. The model is
       ``sentence-transformers/all-MiniLM-L6-v2`` (``EMBEDDING_MODEL``). It is
       not served by Ollama.

Setting ``LLM_PROVIDER=ollama`` changes only the chat model. The embedding model
is loaded locally in both configurations. Its weights are downloaded from
Hugging Face the first time they are needed.

Hardware and disk space
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Item
     - What to expect
   * - Ollama model download
     - ``llama3.2`` is a 3-billion-parameter model. Its download is about
       2 GB, and it is stored under the Ollama data directory.
   * - Embedding model download
     - Small, about 90 MB, cached by Hugging Face under ``~/.cache/huggingface``
       on the host.
   * - RAM
     - The chat model is loaded into memory while it answers. Plan for several
       gigabytes of free RAM for ``llama3.2``. Less capable hardware can use a
       smaller model, such as ``llama3.2:1b``.
   * - GPU
     - Not required. A supported GPU makes answers faster. Check what Ollama
       uses with ``ollama ps`` after a question (the ``PROCESSOR`` column).
   * - First run
     - Both downloads happen once. Answers are slower until the model is loaded
       into memory. The first question also builds the knowledge base.

Step 1: install Ollama
----------------------

Run the official Linux installer on the host:

.. code-block:: bash

   curl -fsSL https://ollama.com/install.sh | sh

The installer places the ``ollama`` command on your ``PATH`` and, on systems
with systemd, starts a background service named ``ollama``. Verify the
installation:

.. code-block:: bash

   ollama --version

Expected: a line such as ``ollama version is 0.x.y``.

.. note::

   **Windows:** install Ollama from `ollama.com/download
   <https://ollama.com/download>`_ and run the commands in this tutorial from
   WSL 2 or from a terminal where Ollama is on the ``PATH``. The
   ``localhost:11434`` address in this tutorial is the same on Windows.

Step 2: start the Ollama service
--------------------------------

Check whether the service is already running:

.. code-block:: bash

   systemctl status ollama --no-pager

Expected: ``Active: active (running)``. If the service is not installed or not
running, start it:

.. code-block:: bash

   sudo systemctl start ollama

If your system has no systemd (for example in WSL without systemd), run the
server in its own terminal instead. Leave this terminal open:

.. code-block:: bash

   ollama serve

Confirm that the API responds. This command works from any terminal:

.. code-block:: bash

   curl http://localhost:11434/api/version

Expected: a JSON object such as ``{"version":"0.x.y"}``.

If you see ``Failed to connect`` or ``Connection refused``, the service is not
running. See :ref:`troubleshooting_ollama_not_running`.

Step 3: download the model
--------------------------

RAGdoll's default model is ``llama3.2``. Download it:

.. code-block:: bash

   ollama pull llama3.2

The command shows download progress and ends with ``success``. The download is
about 2 GB.

Step 4: verify the model is available
-------------------------------------

List the installed models:

.. code-block:: bash

   ollama list

Expected: a row beginning with ``llama3.2:latest``. The name shown in this list
is the value that ``OLLAMA_MODEL`` must match. ``llama3.2`` and
``llama3.2:latest`` refer to the same default tag.

Check the same information through the API:

.. code-block:: bash

   curl http://localhost:11434/api/tags

Expected: a JSON object whose ``models`` array contains an entry with
``"name":"llama3.2:latest"``.

Optionally, ask the model a question directly. This does not involve RAGdoll:

.. code-block:: bash

   ollama run llama3.2 "Reply with one word: ready"

The model prints a short reply and exits. The first run can take a while because
the model is loaded into memory.

.. note::

   If you use a different model, download it with ``ollama pull <name>``, then
   set ``OLLAMA_MODEL`` to the same name as shown by ``ollama list``.

Step 5: configure RAGdoll to use Ollama
---------------------------------------

Open the ``.env`` file in the project directory:

.. code-block:: bash

   cd ~/RAGdoll
   nano .env

Set these three lines. Leave ``OPENAI_API_KEY`` empty or unchanged; it is not
used when the provider is ``ollama``:

.. code-block:: ini

   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2

Check the values:

.. code-block:: bash

   grep -E '^(LLM_PROVIDER|OLLAMA_BASE_URL|OLLAMA_MODEL)=' .env

Expected: the three lines exactly as shown above.

About the Ollama URL
~~~~~~~~~~~~~~~~~~~~

``OLLAMA_BASE_URL`` is the address RAGdoll uses to reach Ollama. The default is
``http://localhost:11434``. Change it only if Ollama runs on another machine or
port, for example ``http://192.168.1.20:11434``. The value is only the base
address. RAGdoll adds the API paths itself.

When RAGdoll runs in Docker, ``localhost`` means the container, not your
host. See :ref:`tutorial_docker_ollama_networking`.

Step 6: start RAGdoll
---------------------

The Ollama service must still be running. Start RAGdoll as in
:ref:`tutorial_local_setup`, step 7:

.. code-block:: bash

   cd ~/RAGdoll
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

Wait for ``Application startup complete``.

Step 7: test the API
--------------------

Open a second terminal and run the health check:

.. code-block:: bash

   curl http://127.0.0.1:8000/health

Expected: ``{"status":"ok"}``.

Ask a question:

.. code-block:: bash

   curl -X POST http://127.0.0.1:8000/api/v1/questions \
     -H "Content-Type: application/json" \
     -d '{"question": "What is GetDP?"}'

The response has the same ``answer`` and ``sources`` fields described in
:ref:`tutorial_local_setup`, step 10. The first question is slower because it
downloads the embedding model (if it is not cached yet) and builds the
knowledge base. While the request runs, ``ollama ps`` in another terminal lists
the loaded model.

Answer quality depends on the model. A 3-billion-parameter model is useful for
testing the pipeline, but it can give shorter or less accurate answers than
larger models or hosted models. Always compare the answer with the ``sources``.

Troubleshooting
---------------

If something fails, see :ref:`tutorial_troubleshooting`. The most common causes
for this tutorial are listed in :ref:`troubleshooting_ollama_not_running`,
:ref:`troubleshooting_ollama_model_missing` and
:ref:`troubleshooting_embedding_download`.
