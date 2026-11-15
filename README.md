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
`http://127.0.0.1:8000/health` for its status. The settings in `.env` are
placeholders and are not yet loaded by the application.

To run the backend in Docker after creating `.env`, use:

```sh
docker compose up --build
```

Ollama is not included in the Compose configuration and must be run separately.