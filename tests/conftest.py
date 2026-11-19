"""Shared pytest configuration for the RAGdoll test suite."""

import pytest

_SETTINGS_ENV_VARS = (
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "EMBEDDING_MODEL",
)


@pytest.fixture
def clean_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove settings-related environment variables for the test's duration.

    Prevents values from the developer's shell from affecting tests.

    :param monkeypatch: Pytest fixture used to unset the variables.
    :type monkeypatch: pytest.MonkeyPatch
    """
    for name in _SETTINGS_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
