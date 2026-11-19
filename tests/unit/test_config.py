"""Unit tests for configuration loading and provider selection."""

import pytest
from pydantic import ValidationError

from app.core.config import LLMProvider, Settings


@pytest.mark.usefixtures("clean_settings_env")
def test_defaults_select_openai_without_api_key() -> None:
    settings = Settings(_env_file=None)

    assert settings.llm_provider is LLMProvider.OPENAI
    assert settings.openai_api_key is None
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


@pytest.mark.usefixtures("clean_settings_env")
def test_provider_is_selected_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")

    settings = Settings(_env_file=None)

    assert settings.llm_provider is LLMProvider.OLLAMA
    assert settings.ollama_model == "mistral"
    assert settings.ollama_base_url == "http://ollama:11434"


@pytest.mark.usefixtures("clean_settings_env")
def test_api_key_is_read_as_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key is not None
    assert "sk-test-secret" not in repr(settings)


@pytest.mark.usefixtures("clean_settings_env")
def test_invalid_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    with pytest.raises(ValidationError, match="llm_provider"):
        Settings(_env_file=None)
