# RAGdoll

RAGdoll is a Python backend skeleton for a retrieval-augmented generation (RAG)
application. Functionality will be implemented incrementally.

## Planned stack

- FastAPI for the HTTP API
- LangChain and LangGraph for document processing and RAG orchestration
- ChromaDB for vector storage and Hugging Face sentence-transformers for embeddings
- OpenAI and Ollama as cloud and local LLM providers
- pytest and HTTPX for testing, Ruff for linting and formatting, and Docker for deployment

ChromaDB and its LangChain integration are not yet dependencies: the current
ChromaDB release has reported security vulnerabilities with no available fix.
They will be added when a safe release is available.

## Repository structure

```text
app/
  main.py             FastAPI entry point
  api/                HTTP routes
  core/               Configuration
  services/           Application services
  rag/                RAG workflow, state, retrieval, and prompts
  infrastructure/     LLM, embedding, and vector store integrations
data/documents/       Source documents
scripts/              Utility scripts
tests/                Automated tests
```

## Local setup

Install Python 3.12 or newer and [uv](https://docs.astral.sh/uv/), then run:

```sh
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

The development server listens on `http://127.0.0.1:8000`; check
`http://127.0.0.1:8000/health` for its status. Settings are read from `.env`
and environment variables; see `.env.example` for the available options. The
default provider is OpenAI (requires `OPENAI_API_KEY`); set `LLM_PROVIDER=ollama`
to use a local Ollama server instead.

## Question API

`POST /api/v1/questions` accepts `{"question": "..."}` and returns the answer
with its sources:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the document say about X?"}'
```

```json
{
  "answer": "...",
  "sources": [
    {"document_name": "guide.md", "section": "Setup", "content": "...", "metadata": {}}
  ]
}
```

Errors: `422` for invalid input, `502` when generation fails, `503` when the
retrieval backend or model is unavailable, and `500` for unexpected errors.
The vector store is currently empty, so answers will report that the context
does not contain enough information until documents are ingested.

To run the backend in Docker after creating `.env`, use:

```sh
docker compose up --build
```

Ollama is not included in the Compose configuration and must be run separately.

## Testing and code quality

After `uv sync`, run the same checks as the CI workflow
(`.github/workflows/ci.yml`):

```sh
uv run pytest                    # run the test suite
uv run ruff check .              # lint
uv run ruff format --check .     # verify formatting
uv run ruff format .             # apply formatting fixes
```

To match CI exactly and fail if `uv.lock` is out of date, add `--locked` to
each command, for example `uv run --locked pytest`.