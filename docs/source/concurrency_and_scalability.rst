.. _concurrency_and_scalability:

Concurrency and scalability
===========================

RAGdoll is a small, single-process service. This page describes how it handles
concurrent requests today, and how it could evolve to serve many users or a
production workload. It is an architectural discussion. None of the proposed
changes are implemented, and the code is not modified by this documentation.

The guiding rule is to keep the current implemented behaviour clearly separate
from what is only proposed. The table below summarises the current state.

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Topic
     - Status
     - Current behaviour
   * - Request handling
     - Implemented
     - ``POST /api/v1/questions`` is a synchronous ``def`` route.
   * - Process model
     - Implemented
     - One Uvicorn process, as in the Dockerfile's ``CMD``. No ``--workers``.
   * - Service initialisation
     - Implemented
     - Built lazily once per process by ``get_question_service``.
   * - Vector store
     - Implemented
     - In-memory, per process, exhaustive search.
   * - LLM and embedding calls
     - Implemented
     - Synchronous calls. No explicit timeout or retry configuration in RAGdoll.
   * - Persistent storage, caching, rate limiting, background ingestion,
       metrics
     - Proposed
     - Not implemented. See the sections below.

Synchronous and asynchronous request processing
-----------------------------------------------

A web server must accept requests while some of them are waiting for slow
operations. There are two ways to do this in Python.

* **Asynchronous** handlers (``async def``) run on one event loop. While a
  handler awaits a network response, the loop serves other requests. This suits
  I/O-bound work such as calls to a remote LLM API.
* **Synchronous** handlers (``def``) are run by FastAPI in a worker thread
  taken from a thread pool, so the event loop is not blocked by them. The
  number of threads is limited, by default to 40 through AnyIO's capacity limiter.

RAGdoll uses the second form for the question route. The handler is a plain
``def``:

.. literalinclude:: ../../app/api/routes.py
   :pyobject: ask_question
   :language: python

This is a sound choice for the current code, because the work inside the handler
is blocking and written with synchronous libraries. An ``async def`` handler
would block the event loop on every call, which is worse. The trade-off is a
bounded number of simultaneous questions, equal to the thread pool size, and
each question holds a thread until it finishes.

FastAPI concurrency and its limits
----------------------------------

FastAPI and Starlette provide the framework's concurrency model, but they do not
make blocking code fast. The main limits are:

* **Blocking calls in ``async def``** stall every request on the same loop. This
  is the most common performance bug in FastAPI services.
* **The thread pool is finite.** When all threads are busy, further requests
  wait in a queue, and latency rises without an obvious error.
* **Threads share one process.** They share memory, the GIL for Python code, and
  the same vector store. CPU-bound work, such as embedding, is limited by the
  GIL in pure Python, although the embedding library releases it for much of its
  computation.
* **One process uses one CPU core for Python bytecode.** Scaling beyond that
  requires more processes.

Blocking LLM and embedding operations
-------------------------------------

Two operations in the request path are slow and blocking:

1. **Embedding the question.** The local Sentence Transformers model runs on
   the CPU, or on a GPU if one is available. It is usually much faster than the
   LLM call, but it still holds a worker thread for the duration of the
   computation.
2. **Calling the chat model.** The OpenAI or Ollama request is an I/O wait of
   seconds, during which the thread is idle but still occupied.

The LLM call dominates latency. The embedding call is cheap, but the model is
heavy in memory, and each process loads its own copy.

Thread pools and worker processes
---------------------------------

Two standard ways to add capacity are:

* **More worker threads** for I/O-bound work, such as waiting on the LLM. This
  is limited by the GIL for Python code, and by the pool size.
* **More worker processes**, each running its own event loop and copy of the
  service, for CPU-bound work. Uvicorn's ``--workers`` option or Gunicorn with
  Uvicorn workers provides this.

The second option has a cost, which is that every process builds its own
knowledge base and holds its own copy of the embedding model. This matters for
the in-memory vector store, discussed below.

Concurrent requests to LLM providers
------------------------------------

A single RAGdoll process can have many LLM calls in flight, and the provider
must accept them. The relevant constraints are:

* **Rate limits.** OpenAI and other providers limit requests and tokens per
  minute per key. Exceeding them returns HTTP 429. A service that sends bursts
  of questions must queue or back off to stay under the limit.
* **Connection pooling.** The OpenAI SDK, used through ``langchain-openai``,
  keeps a pool of HTTP connections. Reusing connections avoids a TLS handshake
  per request. RAGdoll creates the chat model once, so the pool is reused across
  requests.
* **Local models.** Ollama processes requests on the local server. Its own
  concurrency settings determine how many run in parallel, and extra requests
  queue behind them. The application cannot make a local model faster by sending
  more requests.

Timeouts, retries and failure handling
--------------------------------------

RAGdoll does not configure timeouts or retries in its own code. It relies on the
defaults of the client libraries. The OpenAI Python SDK, for example, uses a
default timeout of 600 seconds and retries transient failures twice, which are
the library's documented defaults at the time of writing. These defaults are
long enough that a stalled request can occupy a thread for minutes.

The application already distinguishes failures in its API:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Failure
     - HTTP status
     - Source
   * - Retrieval fails
     - 503
     - ``RAGRetrievalError`` mapped to ``RetrievalFailedError``.
   * - Generation fails
     - 502
     - ``RAGGenerationError`` mapped to ``GenerationFailedError``.
   * - Unexpected error
     - 500
     - Logged with a traceback and returned as a generic message.
   * - Service not initialised
     - 503
     - The question service cannot be built.

A production design would set explicit timeouts for each provider, retry only
idempotent or transient errors with exponential backoff and jitter, and add a
circuit breaker that stops calling a provider that is failing. These are proposed
changes, not current behaviour.

Lazy initialisation and its concurrency implications
----------------------------------------------------

``get_question_service`` is decorated with ``functools.lru_cache``, so the
service is built on the first request and reused afterwards. The code is
described in :ref:`rag_frameworks`.

.. literalinclude:: ../../app/api/dependencies.py
   :pyobject: get_question_service
   :language: python

Lazy initialisation has three concurrency consequences:

* **The first requests are slow.** They load the documents, embed every chunk,
  and load the embedding model. The first user pays this cost.
* **The cache does not lock.** ``lru_cache`` does not guarantee that the
  function runs only once. If several requests arrive during the first build,
  each may run the build, and only one result is kept. This wastes CPU and
  memory but does not corrupt the service, because the result is complete.
* **Failures are not cached.** ``lru_cache`` stores only successful return
  values, so a failed build is retried on the next request. This is intentional,
  because a transient failure should not disable the service until the process
  restarts.

An explicit lock or a start-up hook would make the initialisation deterministic.
Building the knowledge base during application start-up, instead of on the first
request, would move the cost out of user latency. Neither is implemented.

Why an in-memory vector store does not scale out
------------------------------------------------

The vector store is an ``InMemoryVectorStore``, built inside each process (see
:ref:`rag_vector_stores`). It has three limitations for multiple instances:

* **Each instance holds its own copy.** Memory grows linearly with the number of
  instances, and each copy embeds the same chunks again at start-up.
* **Changes are not shared.** Adding or removing documents requires restarting
  every instance, and until all are restarted, they may serve different
  content.
* **Search is exhaustive and process-local.** The cost of a query grows with the
  number of chunks, and no instance can use the index of another.

For the current dataset of 37 chunks this is acceptable. It is not acceptable
for a large corpus or for horizontal scaling.

Persistent vector databases and shared storage
----------------------------------------------

The proposed remedy is a persistent vector database, shared by all instances.
The application would index documents once, store the vectors and metadata, and
have every instance query the same store. Options and their trade-offs are
summarised in :ref:`rag_vector_stores`.

Moving to a shared store also needs:

* a **record of the embedding model** used to build the index, so that an index
  built with one model is not queried with another (see :ref:`rag_embeddings`);
* a **versioned ingestion** process, so that a re-index can replace the index
  atomically;
* **access control** on the store, which is not needed while the data is public.

Horizontal scaling
------------------

Horizontal scaling means adding instances behind a load balancer. For it to
work, the service must be *stateless* from the point of view of a request. The
current design is stateless apart from the per-process knowledge base, which is
rebuilt identically in each process. The consequences are:

* the knowledge base and the embedding model must be loaded by every instance,
  which is wasteful and slow to start;
* a shared vector store removes this duplication and allows instances to start
  quickly;
* the Docker Compose file currently runs one container, and the ``data/documents``
  directory is mounted read-only into it.

Caching opportunities
---------------------

Several results are worth caching, with different risks:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Cache
     - Benefit
     - Risk and invalidation
   * - Query embeddings
     - Avoids recomputing the embedding of a repeated question.
     - Must be invalidated when the embedding model changes.
   * - Retrieval results
     - Avoids repeated vector search.
     - Must be invalidated when the documents are re-indexed.
   * - Final answers
     - Avoids LLM cost and latency for repeated questions.
     - Answers may become stale and must be keyed on the model and the index
       version.
   * - Provider responses
     - Reduces cost and rate-limit pressure.
     - Only safe when the answer does not depend on randomness or time.

Caching should be keyed on the model name and index version, so that a change to
either invalidates the cache automatically. None of these caches is implemented.

Background document ingestion and re-indexing
---------------------------------------------

At present the documents are read once, at the first request, and never
re-read. A production system would separate ingestion from serving:

1. A background job detects changed or new documents.
2. The job loads, splits, and embeds only the changed documents.
3. The new vectors are written to the store, and the old ones are removed.
4. Queries use the new index once it is complete.

This keeps user latency independent of ingestion and allows the index to be
updated without restarting the service. The cost is the complexity of managing
versions and of deleting the chunks of a removed document. Ingestion is not
implemented in RAGdoll.

Monitoring, logging and performance metrics
-------------------------------------------

RAGdoll logs initialisation success and failure, and it logs unexpected
exceptions with a traceback. Failures in the service are logged without
configuration values. It does not currently expose metrics.

A production deployment would track at least the following:

* request count, latency percentiles, and error rate per endpoint and status;
* time spent in retrieval, in embedding, and in the LLM call, so that the
  bottleneck can be identified;
* the number of tokens sent and received, and the cost they represent;
* provider rate-limit responses and retries;
* the size of the knowledge base and the time taken by the last index build.

These measurements are typically exported in a standard format, such as
Prometheus metrics, with distributed tracing through OpenTelemetry to follow a
request across retrieval and generation.

Proposed future architecture
----------------------------

The diagram below shows one possible evolution. Components marked *proposed* do
not exist in the repository.

.. code-block:: text

   Clients
      |
      v
   Load balancer                                   (proposed)
      |
      +--------------------+--------------------+
      |                    |                    |
      v                    v                    v
   RAGdoll API         RAGdoll API          RAGdoll API     (replicated, stateless)
   (Uvicorn workers)   (Uvicorn workers)    (Uvicorn workers)
      |                    |                    |
      +-----------+--------+--------+-----------+
                  |                 |
                  v                 v
        Vector database       Response cache        (proposed)
        (persistent,          (proposed)
         shared)                    |
                  ^                 |
                  |                 v
        Ingestion job          LLM provider with
        (proposed)             rate limits, timeouts,
        re-indexes changed     retries, and a circuit
        documents              breaker              (proposed)
                                    |
                                    v
                       Metrics and logs              (proposed)
                       (Prometheus, OpenTelemetry)

Each proposed improvement, its motivation, and its technology
-------------------------------------------------------------

The table below lists each improvement with the problem it solves, why the
current implementation does not need it yet, and a possible technology.

.. list-table::
   :header-rows: 1
   :widths: 22 30 24 24

   * - Improvement
     - Problem it solves
     - Why it is not needed yet
     - Possible technology
   * - Persistent vector store
     - Shared, persistent index for several instances.
     - The corpus is 37 chunks, and one process is enough.
     - pgvector, Qdrant, Weaviate, Milvus.
   * - Horizontal scaling
     - Throughput beyond one process.
     - Load is low, and the process-local index is cheap.
     - Container orchestration (Kubernetes), a load balancer.
   * - Explicit timeouts and retries
     - Stalled requests holding threads for minutes.
     - Low traffic, and the defaults are acceptable for development.
     - Client configuration, ``tenacity``, or provider SDK settings.
   * - Circuit breaker
     - Repeated calls to a failing provider.
     - A single provider with no measured outages.
     - ``pybreaker``, or a service mesh.
   * - Rate limiting and queueing
     - Exceeding provider limits under bursty load.
     - No measured load against the provider's limits.
     - A token-bucket limiter, a task queue such as Celery or RQ.
   * - Async LLM client
     - More concurrent questions per process without threads.
     - The thread pool handles current load.
     - ``httpx`` with async clients, ``ainvoke`` in LangChain.
   * - Start-up initialisation
     - First-request latency and a non-deterministic first build.
     - A single process rebuilds the index quickly.
     - Application lifespan events in FastAPI.
   * - Response and retrieval cache
     - Repeated LLM calls and vector searches.
     - Not justified without measured repetition of questions.
     - Redis, or an in-process cache with a TTL.
   * - Background ingestion
     - Re-indexing without restarting the service.
     - Documents change rarely and the index is rebuilt at start-up.
     - A scheduled job, a message queue, and versioned indexes.
   * - Metrics and tracing
     - Diagnosing latency and cost.
     - Not yet needed at this scale, and the logs are sufficient for development.
     - Prometheus, OpenTelemetry.

Further reading
---------------

* FastAPI, *Concurrency and async / await*:
  https://fastapi.tiangolo.com/async/
* Uvicorn, *Deployment*: https://www.uvicorn.org/deployment/
* Python documentation, ``functools.lru_cache``:
  https://docs.python.org/3/library/functools.html#functools.lru_cache
* OpenAI, *Rate limits*: https://platform.openai.com/docs/guides/rate-limits
* OpenTelemetry documentation: https://opentelemetry.io/docs/

