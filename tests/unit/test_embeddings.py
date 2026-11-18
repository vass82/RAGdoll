"""Unit tests for the embedding factory.

``HuggingFaceEmbeddings`` is replaced with a recording fake so the tests do not
download model weights.
"""

from typing import Any

import pytest

from app.core.config import Settings
from app.infrastructure import embeddings as embeddings_module


class RecordingEmbeddings:
    """Stand-in for ``HuggingFaceEmbeddings`` that records its constructor arguments."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


@pytest.mark.usefixtures("clean_settings_env")
def test_embeddings_use_configured_local_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(embeddings_module, "HuggingFaceEmbeddings", RecordingEmbeddings)
    settings = Settings(_env_file=None, embedding_model="BAAI/bge-small-en-v1.5")

    embeddings = embeddings_module.create_embeddings(settings)

    assert isinstance(embeddings, RecordingEmbeddings)
    assert embeddings.kwargs == {"model_name": "BAAI/bge-small-en-v1.5"}
