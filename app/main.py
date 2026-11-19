"""FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="RAGdoll", version="0.1.0")
app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Report that the API process is running.

    This check does not contact the language model or embedding provider.

    :returns: A status payload.
    :rtype: dict[str, str]
    """
    return {"status": "ok"}
