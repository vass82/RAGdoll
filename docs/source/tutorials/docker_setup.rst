.. _tutorial_docker_setup:

Docker setup
============

This tutorial runs the RAGdoll API in a Docker container managed by Docker
Compose. Use it when you want an environment that does not depend on the Python
version or packages installed on your machine.

.. note::

   The container runs **only the API**. The chat model is either the OpenAI
   API or an Ollama server, and the embedding model is downloaded by the
   container on first use. Ollama is never started by the Compose file in this
   repository.

Where commands run
------------------

Each command block is labelled with where it runs:

* **Host**: your Ubuntu terminal, in the RAGdoll project directory.
* **Container**: a shell inside the running ``backend`` container, started with
  ``docker compose exec``.

Unless a command says otherwise, run host commands from the project root:

.. code-block:: console

   $ cd ~/RAGdoll
   $ pwd
   /home/<your-user>/RAGdoll

Step 1. Install Docker Engine and the Compose plugin
----------------------------------------------------

Run these commands on the **host**. They follow the official Docker
installation procedure for Ubuntu (see :ref:`docker_references`).

1. Remove unofficial Docker packages that may conflict (ignore "not installed"
   messages):

   .. code-block:: console

      $ sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc

2. Add Docker's apt repository:

   .. code-block:: console

      $ sudo apt update
      $ sudo apt install -y ca-certificates curl
      $ sudo install -m 0755 -d /etc/apt/keyrings
      $ sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
      $ sudo chmod a+r /etc/apt/keyrings/docker.asc
      $ echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      $ sudo apt update

3. Install Docker Engine, the Buildx plugin and the Compose plugin:

   .. code-block:: console

      $ sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

4. Allow your user to run Docker without ``sudo``. Log out and log back in
   after this command:

   .. code-block:: console

      $ sudo usermod -aG docker $USER

.. warning::

   The ``docker`` group grants root-equivalent access to the machine. Add only
   users you trust.

Step 2. Verify the installation
-------------------------------

Run on the **host**, in a new login session (after step 4):

.. code-block:: console

   $ docker version --format '{{.Server.Version}}'
   <docker-engine-version>
   $ docker compose version
   Docker Compose version <compose-version>

The version numbers you see depend on the release you install. What matters is
that both commands print a version and do not report
``permission denied`` or ``unknown command``.

Then run the test image:

.. code-block:: console

   $ docker run --rm hello-world

Expected result: the output contains ``Hello from Docker!``.

.. note::

   The Ubuntu archive package ``docker-compose`` is the legacy v1 tool, run as
   ``docker-compose`` (with a hyphen). This tutorial uses the v2 plugin, run as
   ``docker compose`` (with a space). If ``docker compose version`` reports an
   unknown command, install ``docker-compose-plugin`` from the repository above.

Step 3. Prepare the environment file
------------------------------------

The Compose file reads the variables from a ``.env`` file in the project root
(``env_file: .env``). Create it on the **host** if you have not done so in the
:ref:`local tutorial <tutorial_local_setup>`:

.. code-block:: console

   $ cd ~/RAGdoll
   $ cp .env.example .env

Edit ``.env`` for your provider. The variables are described in
:ref:`tutorial_configuration`.

For OpenAI, set at least:

.. code-block:: text

   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-real-key

For Ollama running on the host, see
:ref:`tutorial_docker_ollama_networking` before you change ``OLLAMA_BASE_URL``.

.. warning::

   ``.env`` contains your API key. It is listed in ``.gitignore`` and must
   never be committed. The Dockerfile does not copy ``.env`` into the image.
   Instead, Compose passes its values to the container as environment
   variables at start-up.

Step 4. Understand the Dockerfile
---------------------------------

The Dockerfile is in the project root:

.. literalinclude:: ../../../Dockerfile
   :language: dockerfile
   :caption: Dockerfile

What each instruction does:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Instruction
     - Effect
   * - ``FROM python:3.12-slim``
     - Starts from the official slim Python 3.12 image.
   * - ``pip install uv==0.13.8``
     - Installs the pinned uv version used by the project.
   * - ``COPY pyproject.toml README.md`` and ``uv sync --no-dev``
     - Installs the locked runtime dependencies (without development tools) into
       ``/app/.venv``. Because only these files are copied first, Docker reuses
       this layer when only application code changes.
   * - ``COPY app ./app``
     - Copies the application code. Only ``app/`` is copied, so ``data/``,
       ``tests/`` and ``.env`` are not part of the image.
   * - ``CMD ["uvicorn", ...]``
     - Starts the API on port 8000, listening on all interfaces inside the
       container.

The image is large (about 3 GB) because PyTorch, which Sentence Transformers
uses for embeddings, is installed with its CUDA libraries. Building it needs
several gigabytes of free space on the Docker data disk, in addition to the
final image size. If the build fails with ``no space left on device``, see
:ref:`troubleshooting_docker_disk_space`.

Step 5. Understand the Compose file
-----------------------------------

.. literalinclude:: ../../../docker-compose.yml
   :language: yaml
   :caption: docker-compose.yml

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Meaning
   * - ``build: .``
     - Build the image from the Dockerfile in the current directory.
   * - ``ports: "8000:8000"``
     - Publish container port 8000 on host port 8000. The API is then reachable
       at ``http://localhost:8000`` on your Ubuntu machine.
   * - ``env_file: .env``
     - Pass each ``KEY=value`` line of ``.env`` to the container as an
       environment variable.
   * - ``volumes: ./data/documents:/app/data/documents:ro``
     - Mount the host folder ``data/documents`` into the container at the
       location where the application reads documents by default
       (``DOCUMENTS_DIR=data/documents``, relative to ``/app``).

The document mount and why it is read-only
------------------------------------------

The Markdown documents are **not** baked into the image. They are read from the
host folder ``data/documents`` through the bind mount.

The suffix ``:ro`` makes the mount **read-only**. The container can read the
documents but cannot create, modify or delete them. The application only reads
the knowledge base, so this limits the damage a compromised or buggy process
could do to your files on the host.

You can check this after the container starts (see step 7):

.. code-block:: console

   $ docker compose exec backend sh -c 'touch /app/data/documents/test.md'
   touch: cannot touch '/app/data/documents/test.md': Read-only file system

Consequences of the mount:

* Edit or add documents on the **host**, then restart the container so that
  the knowledge base is rebuilt. The application builds the index once per
  process and caches it, so new files are not picked up while the process runs.
* If the host folder is empty or missing, the container starts but answers
  fail. See :ref:`troubleshooting_documents_dir` and
  :ref:`troubleshooting_empty_collection`.

Step 6. Build and start the container
-------------------------------------

Run on the **host**, from the project root (the folder that contains
``docker-compose.yml``):

.. code-block:: console

   $ cd ~/RAGdoll
   $ docker compose up --build -d

What happens:

* ``--build`` builds the image (the first build takes several minutes).
* ``-d`` runs the container in the background.

Expected output ends with lines similar to:

.. code-block:: text

   ✔ Container ragdoll-backend-1  Started

The container name may differ slightly, because Compose uses the project name
(here ``ragdoll``, taken from the directory name) to build it.

Step 7. Access the API
----------------------

Run on the **host**:

.. code-block:: console

   $ curl -s http://localhost:8000/health
   {"status":"ok"}

Then send a question. The command is the same as in the
:ref:`local tutorial <tutorial_local_setup>`:

.. code-block:: console

   $ curl -s -X POST http://localhost:8000/api/v1/questions \
       -H "Content-Type: application/json" \
       -d '{"question": "What is GetDP?"}'

The interactive API documentation (Swagger UI) is at
``http://localhost:8000/docs``. Open it in a browser on the host.

.. note::

   The route is defined in ``app/api/routes.py``: the router prefix is
   ``/api/v1`` and the endpoint is ``POST /questions``.

Step 8. Check the logs and status
---------------------------------

Run on the **host**:

.. code-block:: console

   $ docker compose ps
   $ docker compose logs --tail=50 backend
   $ docker compose logs -f backend      # follow live; press Ctrl+C to stop

A healthy start ends with lines like:

.. code-block:: text

   INFO:     Started server process [1]
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

If you need a shell inside the container (a **container** command), run:

.. code-block:: console

   $ docker compose exec backend sh

From that shell, the application code is in ``/app/app`` and the Python
environment is ``/app/.venv``. Type ``exit`` to return to the host.

.. note::

   The container image has no ``curl`` or ``wget``. To test a URL from inside
   the container, use Python, for example
   ``python -c "import urllib.request as u; print(u.urlopen('http://localhost:8000/health').read())"``.

Step 9. Stop and remove the containers
--------------------------------------

Run on the **host**:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Command
     - Result
   * - ``docker compose stop``
     - Stops the container. It is kept and can be started again with
       ``docker compose start``.
   * - ``docker compose down``
     - Stops and removes the container and the project network. The image is
       kept, so the next ``docker compose up`` is fast.
   * - ``docker compose down --rmi local``
     - Also removes the image built for this project. The next start needs a
       full rebuild.

.. note::

   Hugging Face model files for the embedding model are stored inside the
   container, because the Compose file has no cache volume. Removing the
   container with ``docker compose down`` causes the embedding model to be
   downloaded again on the next start. This is the expected behaviour of this
   configuration.

.. _tutorial_docker_ollama_networking:

Connecting the container to Ollama
----------------------------------

This section applies only when ``LLM_PROVIDER=ollama``. Read
:ref:`tutorial_ollama_setup` first to install and start Ollama.

The key idea is that **every container has its own** ``localhost``.

.. warning::

   Inside the RAGdoll container, ``localhost`` (and ``127.0.0.1``) refers to the
   container itself, **not** to your Ubuntu host. Ollama running on the host is
   therefore not reachable at ``http://localhost:11434`` from the container.
   The connection is refused. You can confirm this:

   .. code-block:: console

      $ docker compose exec backend python -c "import urllib.request as u; u.urlopen('http://localhost:11434/api/version', timeout=3)"
      URLError: <urlopen error [Errno 111] Connection refused>

The table below compares the three possible setups.

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Setup
     - ``OLLAMA_BASE_URL`` in ``.env``
     - Notes
   * - Ollama on the host, RAGdoll on the host (local tutorial)
     - ``http://localhost:11434``
     - No container involved. Works by default.
   * - Ollama on the host, RAGdoll in Docker
     - ``http://host.docker.internal:11434``
     - Requires the override file below and Ollama listening on the Docker
       bridge (see the next subsection).
   * - Ollama in its own container
     - ``http://ollama:11434``
     - Requires adding an ``ollama`` service to your own Compose setup, on the
       same network as ``backend``. The project's Compose file does not define
       it. This option was not tested for this documentation.

Option A: Ollama on the host, RAGdoll in Docker (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Make Ollama listen on the Docker bridge as well as on localhost. On the
   **host**, edit the Ollama systemd service:

   .. code-block:: console

      $ sudo systemctl edit ollama.service

   Add these lines in the editor, save and exit:

   .. code-block:: ini

      [Service]
      Environment="OLLAMA_HOST=0.0.0.0:11434"

   Then restart Ollama on the **host**:

   .. code-block:: console

      $ sudo systemctl daemon-reload
      $ sudo systemctl restart ollama
      $ curl -s http://localhost:11434/api/version
      {"version":"0.x.y"}

   Binding to ``0.0.0.0`` makes Ollama reachable from other machines on the
   network as well, unless a firewall blocks port 11434. If that is a concern,
   restrict access with your firewall.

2. Create a file named ``docker-compose.override.yml`` in the project root on
   the **host**. Docker Compose reads it automatically together with
   ``docker-compose.yml``:

   .. code-block:: yaml

      services:
        backend:
          extra_hosts:
            - "host.docker.internal:host-gateway"

   ``host-gateway`` is a special value that Docker resolves to the host's
   address on the Docker bridge. Docker on Linux does not define
   ``host.docker.internal`` by default, so this line is required.

3. Set the Ollama URL in ``.env`` on the **host**:

   .. code-block:: text

      LLM_PROVIDER=ollama
      OLLAMA_BASE_URL=http://host.docker.internal:11434
      OLLAMA_MODEL=llama3.2

4. Recreate the container so that it picks up the new settings:

   .. code-block:: console

      $ docker compose up -d

   Compose recreates the container with the new environment. Because the image
   is already built, this command is quick.

5. Check the configuration Compose will use (the output includes the host
   mapping):

   .. code-block:: console

      $ docker compose config | grep -A1 extra_hosts
            extra_hosts:
              - host.docker.internal=host-gateway

6. Confirm that the container reaches Ollama:

   .. code-block:: console

      $ docker compose exec backend python -c "import urllib.request as u; print(u.urlopen('http://host.docker.internal:11434/api/version', timeout=5).read())"
      b'{"version":"0.x.y"}'

   If this fails, see :ref:`troubleshooting_docker_ollama_unreachable`.

Option B: Ollama in a separate container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also run Ollama as a service in the same Compose project. This option
requires you to write your own Compose configuration. The project does not
include it, and this documentation does not test it. In outline:

* Add an ``ollama`` service to a Compose override file.
* Put both services on the same network, which Compose does by default.
* Set ``OLLAMA_BASE_URL=http://ollama:11434`` in ``.env``. The service name
  ``ollama`` resolves inside the Compose network.
* Store the models in a named volume, so that they are not downloaded again
  after ``docker compose down``.

Use Option A unless you need Ollama to run inside Docker as well.

Running with OpenAI instead
---------------------------

With OpenAI, no Ollama networking is needed. Set ``LLM_PROVIDER=openai`` and
``OPENAI_API_KEY`` in ``.env``, then run ``docker compose up --build -d``. Your
key is passed to the container only through ``env_file``.

.. _docker_references:

References
----------

* Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
* Docker Compose plugin: https://docs.docker.com/compose/install/linux/
* Compose file reference, ``extra_hosts``: https://docs.docker.com/reference/compose-file/services/#extra_hosts
* Compose ``env_file``: https://docs.docker.com/reference/compose-file/services/#env_file
* Bind mounts and read-only mounts: https://docs.docker.com/engine/storage/bind-mounts/

Next steps
----------

* Choose a provider and understand every setting: :ref:`tutorial_configuration`.
* If something fails: :ref:`tutorial_troubleshooting`.
