.. _tutorial_troubleshooting:

Troubleshooting
===============

This page lists the problems most often seen when running RAGdoll and how to
diagnose them. Start with the **Diagnose first** steps, then go to the section
that matches your symptom.

.. _troubleshooting_diagnose_first:

Diagnose first
--------------

Run these checks on the **host**, from the project root. They tell you whether
the API is running and what it reports.

.. code-block:: console

   $ cd ~/RAGdoll
   $ curl -s -i http://localhost:8000/health

Expected result: a first line ending in ``200 OK`` and the body
``{"status":"ok"}``. If ``curl`` prints ``Failed to connect`` or
``Connection refused``, the API is not running on port 8000. Go to
:ref:`troubleshooting_connection_refused`.

The API logs contain the reason for most start-up failures. Where to read them:

* **Local run:** the terminal in which ``uv run uvicorn ...`` is running.
* **Docker run:** on the host, run ``docker compose logs --tail=100 backend``.

The application logs the reason for knowledge-base problems in full. For other
initialisation failures it logs only the exception type, such as ``OSError`` or
``ValueError``. The matching section below explains each type.

Find the symptom
----------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Symptom
     - Go to
   * - Question returns ``503`` and the log shows ``ValueError``
     - :ref:`troubleshooting_missing_api_key`
   * - Question returns ``503`` and the log shows ``OSError``
     - :ref:`troubleshooting_embedding_download`
   * - Question returns ``502``
     - :ref:`troubleshooting_ollama_not_running`,
       :ref:`troubleshooting_ollama_model_missing`
   * - ``curl`` says ``Connection refused``
     - :ref:`troubleshooting_connection_refused`
   * - Log says ``Could not load documents from ...``
     - :ref:`troubleshooting_documents_dir`
   * - Log says ``No Markdown documents found in ...``
     - :ref:`troubleshooting_empty_collection`
   * - The first question takes a long time
     - :ref:`troubleshooting_slow_first_request`
   * - Model download fails or hangs
     - :ref:`troubleshooting_embedding_download`
   * - Docker says ``no space left on device``
     - :ref:`troubleshooting_docker_disk_space`
   * - Container cannot see documents, or the mount is read-only when you expect
     - :ref:`troubleshooting_docker_mount`
   * - Container cannot reach Ollama on the host
     - :ref:`troubleshooting_docker_ollama_unreachable`
   * - ``address already in use`` or ``port is already allocated``
     - :ref:`troubleshooting_port_conflict`

.. _troubleshooting_missing_api_key:

Missing or empty OpenAI API key
-------------------------------

**Symptom.** A question returns HTTP ``503`` with the detail
``The question service is not available.`` The log shows
``Question service initialisation failed: ValueError``.

**Likely causes.**

* ``OPENAI_API_KEY`` is missing from ``.env``, or it is empty.
* ``LLM_PROVIDER`` is ``openai``, which is the default, but you meant to use
  Ollama.
* You edited ``.env`` but did not restart the server or the container. The
  settings are read when the process starts.

**Diagnose.**

.. code-block:: console

   $ cd ~/RAGdoll
   $ grep -E '^(LLM_PROVIDER|OPENAI_API_KEY)=' .env | sed -E 's/(OPENAI_API_KEY=).{4,}/\1****REDACTED****/'

The command hides the key and shows whether it is set. Expected result for
OpenAI:

.. code-block:: text

   LLM_PROVIDER=openai
   OPENAI_API_KEY=****REDACTED****

If ``OPENAI_API_KEY=`` has nothing after the ``=``, the key is empty. Add your
key and restart. For Docker, run ``docker compose up -d`` again so that the
container is recreated with the new values.

**Fix.** Set ``OPENAI_API_KEY`` to a real key, or set ``LLM_PROVIDER=ollama``
and follow :ref:`tutorial_ollama_setup`.

.. _troubleshooting_documents_dir:

Missing document directory
--------------------------

**Symptom.** The question returns ``503``. The log shows:

.. code-block:: text

   Could not load documents from data/documents.

**Likely causes.**

* You started the server from a directory other than the project root. The
  default ``DOCUMENTS_DIR=data/documents`` is relative to the **current working
  directory**.
* The folder was moved or renamed, or ``DOCUMENTS_DIR`` points to a path that
  does not exist.

**Diagnose.**

.. code-block:: console

   $ pwd
   $ ls -ld data/documents
   $ ls data/documents

Expected result: ``pwd`` prints the RAGdoll project root, and ``ls`` lists
``README.md``, ``command_line.md`` and other Markdown files. If ``ls`` reports
``No such file or directory``, you are in the wrong directory, or the folder is
missing.

**Fix.** Run ``cd ~/RAGdoll`` before starting the server. Alternatively, set
``DOCUMENTS_DIR`` to an absolute path in ``.env``. In Docker, see
:ref:`troubleshooting_docker_mount`.

.. _troubleshooting_empty_collection:

Empty document collection
-------------------------

**Symptom.** The question returns ``503``. The log shows:

.. code-block:: text

   No Markdown documents found in data/documents.

**Likely causes.**

* The folder exists but contains no files ending in ``.md``. Only Markdown
  files are loaded.
* The files are in a subfolder that is not in ``DOCUMENTS_DIR``.

**Diagnose.**

.. code-block:: console

   $ cd ~/RAGdoll
   $ find data/documents -name '*.md' | head

Expected result: a list of ``.md`` paths. An empty result means there is
nothing to index.

**Fix.** Restore the Markdown files from the repository (``git checkout --
data/documents``) or copy your own ``.md`` files into the folder. Then restart
RAGdoll, because the knowledge base is built once per process.

.. note::

   A **non-empty** collection can still give the answer *"I could not find any
   relevant information in the knowledge base to answer this question."* This
   means retrieval found no chunks, and the chat model was not called. It is
   not a configuration error.

.. _troubleshooting_ollama_not_running:

Ollama not running
------------------

**Symptom.** With ``LLM_PROVIDER=ollama``, a question returns HTTP ``502`` with the
detail ``The language model failed to generate an answer.`` The server log
contains ``Generation failed:`` followed by an exception type, for example a
connection error.

**Likely causes.**

* The Ollama service is stopped.
* RAGdoll runs on the host while ``OLLAMA_BASE_URL`` points to another address.

**Diagnose** (on the **host**):

.. code-block:: console

   $ systemctl status ollama --no-pager
   $ curl -s http://localhost:11434/api/version

Expected result: the service is ``active (running)``, and ``curl`` prints a
JSON object with ``"version"``.

**Fix.** Start the service with ``sudo systemctl start ollama``. See
:ref:`tutorial_ollama_setup`.

.. _troubleshooting_ollama_model_missing:

Ollama model not downloaded
---------------------------

**Symptom.** The question returns ``502``. The log contains ``Generation failed:``
and the Ollama server reports that the model was not found.

**Likely causes.** ``OLLAMA_MODEL`` names a model you have not pulled, or the
name differs from the downloaded one. The default is ``llama3.2``.

**Diagnose** (on the **host**):

.. code-block:: console

   $ ollama list
   $ curl -s http://localhost:11434/api/tags

Expected result: the model named in ``OLLAMA_MODEL`` appears in the list.

**Fix.** Download it with ``ollama pull llama3.2``, or change ``OLLAMA_MODEL`` to
a model shown by ``ollama list``. Restart RAGdoll afterwards.

.. _troubleshooting_connection_refused:

Connection refused
------------------

**Symptom.** ``curl`` prints ``Failed to connect to localhost port 8000`` or
``Connection refused``. This can also appear for Ollama, on port 11434.

**Likely causes.**

* The API server is not running. You closed the terminal, or it stopped after
  an error.
* The API is running on another port or address. The local tutorial binds to
  ``127.0.0.1:8000``.
* For Ollama, the service is not running, or it listens only on ``127.0.0.1``
  while a container tries to reach it.

**Diagnose.**

.. code-block:: console

   $ ss -ltnp | grep -E ':(8000|11434)\b'

Expected result when both services run: lines for ``127.0.0.1:8000`` or
``0.0.0.0:8000`` (the API), and for ``:11434`` (Ollama). If a port is missing,
that service is not listening.

In Docker, run ``docker compose ps``. The ``backend`` service should show
``running`` and the port mapping ``0.0.0.0:8000->8000/tcp``.

**Fix.** Start the server again (:ref:`tutorial_local_setup`, step 10) or the
container (``docker compose up -d``). For a container that cannot reach Ollama,
see :ref:`troubleshooting_docker_ollama_unreachable`.

.. _troubleshooting_slow_first_request:

Slow first request
------------------

**Symptom.** The first question takes from tens of seconds to a few minutes.
Later questions are much faster.

**Likely causes.** This is expected. The first request builds the question
service, which:

* loads the embedding model (on the first run, it is downloaded from Hugging
  Face);
* reads, splits and indexes all Markdown documents;
* on the first run with Ollama, may load the chat model into memory.

The service is then cached for the life of the process. Only the first request
pays this cost, unless the service restarts.

**Diagnose.** Watch the log while you send the first question. The lines before
the answer show progress. If there is no log output for several minutes, see
:ref:`troubleshooting_embedding_download`.

**Fix.** Nothing is required. To avoid the delay in a demo, send one warm-up
question after start-up. The first question in Docker is slower than in a local
run, because the container starts with an empty model cache (see
:ref:`tutorial_docker_setup`).

.. _troubleshooting_embedding_download:

Embedding model download problems
---------------------------------

**Symptom.** The first question returns ``503``, sometimes after a long delay.
The log shows ``Question service initialisation failed: OSError``. This happens
when the embedding model cannot be downloaded from Hugging Face.

**Likely causes.**

* No internet access, or a proxy or firewall blocks ``huggingface.co``.
* The disk is full, so the model cannot be stored.
* ``EMBEDDING_MODEL`` names a model that does not exist.

**Diagnose** (on the **host**):

.. code-block:: console

   $ curl -sI https://huggingface.co | head -n 1
   $ df -h ~ | tail -n 1
   $ ls ~/.cache/huggingface/hub 2>/dev/null | head

Expected result: ``HTTP/2 200`` (or a redirect code), free disk space, and a
folder whose name starts with ``models--sentence-transformers``. If the cache
folder is missing after a failed start, the download did not complete.

In Docker, the cache lives inside the container, so run the diagnostic inside
it:

.. code-block:: console

   $ docker compose exec backend python -c "import urllib.request as u; print(u.urlopen('https://huggingface.co', timeout=10).status)"

**Fix.** Make sure the machine can reach ``huggingface.co``, and that the disk
has space. Then restart RAGdoll and send the question again. A failed build is
not cached, so the next request retries the download.

.. _troubleshooting_docker_disk_space:

Docker build fails: no space left on device
-------------------------------------------

**Symptom.** ``docker compose up --build`` fails while extracting layers, with
``no space left on device``.

**Likely causes.** The image is about 3 GB because it contains the PyTorch
CUDA libraries. The build needs several gigabytes of temporary space as well.
Old images and build cache also use space.

**Diagnose** (on the **host**):

.. code-block:: console

   $ df -h /var/lib/docker | tail -n 1
   $ docker system df

**Fix.** Remove unused data. This deletes stopped containers, unused networks,
dangling images and build cache, but it keeps images in use:

.. code-block:: console

   $ docker system prune -f
   $ docker builder prune -af

Then build again. If the disk is still too small, free space on the disk or
move Docker's data directory. Read the Docker documentation before you move it.

.. _troubleshooting_docker_mount:

Docker volume mount problems
----------------------------

**Symptom.** The container starts, but the log shows the empty-collection or
missing-directory messages, or changes you make on the host are not reflected.

**Likely causes.**

* You ran ``docker compose`` from a directory other than the project root, so
  ``./data/documents`` refers to a different folder.
* ``data/documents`` did not exist on the host. Docker creates a missing bind
  mount directory itself, and that directory is owned by ``root`` and is empty.
* The container was not restarted after you changed the documents. The index is
  built once per process.
* The mount is read-only by design (``:ro``), so the application cannot write
  into it. This is expected.

**Diagnose** (on the **host**, then in the **container**):

.. code-block:: console

   $ cd ~/RAGdoll
   $ ls -la data/documents | head
   $ docker compose exec backend sh -c 'ls /app/data/documents | head; grep documents /proc/mounts'

Expected result: the host folder lists the ``.md`` files, and the container
shows the same files under ``/app/data/documents``. ``mount`` shows the mount
with the ``ro`` option.

If the container shows nothing, check that ``docker compose config`` prints a
``volumes`` entry with the source path ``.../RAGdoll/data/documents``.

**Fix.** Run Compose from the project root, make sure ``data/documents`` holds
the files, and restart the container with ``docker compose restart backend``.
If Docker created an empty root-owned folder, remove it with
``sudo rmdir data/documents`` (only if it is empty) and restore the files.

.. _troubleshooting_docker_ollama_unreachable:

Container cannot reach Ollama on the host
-----------------------------------------

**Symptom.** With ``LLM_PROVIDER=ollama`` in Docker, questions return ``502``.
Inside the container, ``localhost:11434`` gives ``Connection refused``.

**Likely causes.**

* ``OLLAMA_BASE_URL`` still uses ``localhost``. Inside a container, that means
  the container itself.
* The ``extra_hosts`` override is missing, so ``host.docker.internal`` does not
  resolve.
* Ollama listens only on ``127.0.0.1``, so the Docker bridge cannot reach it.

**Diagnose.**

.. code-block:: console

   $ docker compose exec backend python -c "import socket; print(socket.gethostbyname('host.docker.internal'))"
   $ docker compose exec backend python -c "import urllib.request as u; print(u.urlopen('http://host.docker.internal:11434/api/version', timeout=5).read())"

Expected result: an IP address (usually ``172.17.0.1``), then a JSON version
string. If the first command fails with ``gaierror``, the override is missing.
If the second command fails with ``Connection refused``, Ollama is not listening
on the bridge address.

**Fix.** Follow :ref:`tutorial_docker_ollama_networking`: create
``docker-compose.override.yml`` with ``extra_hosts``, set
``OLLAMA_BASE_URL=http://host.docker.internal:11434``, configure
``OLLAMA_HOST=0.0.0.0:11434`` for the Ollama service, then run
``docker compose up -d``.

.. _troubleshooting_port_conflict:

Port conflicts
--------------

**Symptom.** Uvicorn prints ``[Errno 98] address already in use``. Docker
prints ``Bind for 0.0.0.0:8000 failed: port is already allocated``.

**Likely causes.** Another process, often an earlier RAGdoll server or
container, is already using port 8000.

**Diagnose** (on the **host**):

.. code-block:: console

   $ ss -ltnp | grep ':8000\b'
   $ docker ps --format 'table {{.Names}}\t{{.Ports}}'

Expected result when the port is free: no output from the first command. The
second command lists the container that holds the port, if any.

**Fix.** Stop the other process or container. For example, run
``docker compose down`` in the earlier project folder, or stop the old server
with ``Ctrl+C`` in its terminal. If you must keep the other service, change the
host port in the Compose file, for example ``"8080:8000"``, and then use
``http://localhost:8080``. For a local run, use another port with
``uv run uvicorn app.main:app --host 127.0.0.1 --port 8080``.

Still stuck?
------------

Collect this information before you ask for help:

* The output of ``curl -s -i http://localhost:8000/health``.
* The last 50 log lines (terminal output, or ``docker compose logs --tail=50 backend``).
* The provider settings, without the API key: ``LLM_PROVIDER`` and
  ``OLLAMA_MODEL`` or ``OPENAI_MODEL``. Never share the key itself.

Related pages: :ref:`tutorial_configuration`, :ref:`tutorial_local_setup`,
:ref:`tutorial_ollama_setup`, :ref:`tutorial_docker_setup`.
