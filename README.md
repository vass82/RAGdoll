# RAGdoll

RAGdoll is a Python backend for question answering over Markdown documents using
retrieval-augmented generation (RAG). A client sends a question to the HTTP API;
the service retrieves the most relevant document passages, passes them to a
language model, and returns the answer together with its sources.

Documentation: <https://vass82.github.io/RAGdoll/>

## Implemented features

- HTTP API built with FastAPI (`GET /health`, `POST /api/v1/questions`).
- RAG workflow built with LangGraph: retrieval followed by generation.
- Loading, chunking, embedding, and indexing of Markdown documents from `data/documents/`.
- Local embeddings with Sentence Transformers (no API key required).
- In-memory vector store, rebuilt when the process starts.
- OpenAI (default) or Ollama (local) as the chat model provider.
- Lazy knowledge-base initialization on the first question request.
- Automated tests, Ruff checks, Docker Compose support, and GitHub Actions CI.

Not implemented yet: persistent or shared vector storage, streaming responses,
conversation memory, and advanced retrieval such as metadata filtering, hybrid
search, or reranking. The Sphinx documentation discusses these as possible future
work. ChromaDB is one candidate for a future persistent store; it is not a dependency.

## Technology stack

| Concern            | Implementation                                             |
|--------------------|------------------------------------------------------------|
| HTTP API           | FastAPI, served by Uvicorn                                 |
| RAG workflow       | LangGraph on top of LangChain                              |
| Document splitting | `langchain-text-splitters`                                 |
| Embeddings         | Sentence Transformers via `langchain-huggingface`          |
| Vector store       | LangChain `InMemoryVectorStore`                            |
| Chat model         | OpenAI (`langchain-openai`) or Ollama (`langchain-ollama`) |
| Configuration      | pydantic-settings, from environment variables and `.env`   |
| Tests and lint     | pytest, HTTPX, Ruff, pytest-cov                            |

## Repository structure

```text
app/
  main.py             FastAPI application and /health endpoint
  api/                Routes, request and response schemas, dependency wiring
  core/               Settings (environment variables and .env)
  services/           Knowledge-base construction and question service
  rag/                Chunking, indexing, retrieval, prompts, LangGraph workflow
  infrastructure/     Document loader, embedding, vector store, and LLM factories
data/documents/       Markdown source documents
docs/source/          Sphinx documentation
scripts/              build_docs.sh (tests with coverage, then Sphinx build)
tests/                unit/ and integration/ test suites
```

## Quick start

Requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```sh
cp .env.example .env     # set OPENAI_API_KEY, or LLM_PROVIDER=ollama
uv sync
uv run uvicorn app.main:app --reload
```

The server listens on `http://127.0.0.1:8000`. The first question request builds
the knowledge base, which can take longer because documents are embedded and the
embedding model may be downloaded. See the
[local setup tutorial](https://vass82.github.io/RAGdoll/tutorials/local_setup.html)
and the [configuration reference](https://vass82.github.io/RAGdoll/tutorials/configuration.html).

## HTTP API

```sh
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the document say about X?"}'
```

The response contains `answer` and `sources`. While the server runs, interactive
FastAPI documentation is available at `/docs`. The full endpoint, schema, and
status-code reference is in the [HTTP API documentation](https://vass82.github.io/RAGdoll/http_api.html).

## Docker Compose

After creating `.env`, build and start the backend:

```sh
docker compose up --build
```

The API is published on port 8000. Ollama is not included in the Compose file and
must be run separately. See the [Docker tutorial](https://vass82.github.io/RAGdoll/tutorials/docker_setup.html).

## Testing and code quality

```sh
uv run pytest                    # run the test suite
uv run ruff check .              # lint
uv run ruff format --check .     # check formatting
```

CI runs these commands with `--locked` (see `.github/workflows/ci.yml`).

## Documentation

The Sphinx documentation is published to GitHub Pages at
<https://vass82.github.io/RAGdoll/>. To build it locally:

```sh
bash scripts/build_docs.sh
```

The generated HTML is written to `docs/_build/html/`.

## License

Released under the MIT License. See [LICENSE](LICENSE).

