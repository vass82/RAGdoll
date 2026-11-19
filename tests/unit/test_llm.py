"""Unit tests for the chat model factory."""

import pytest
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.infrastructure.llm import create_chat_model


@pytest.mark.usefixtures("clean_settings_env")
def test_openai_provider_creates_openai_chat_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        openai_api_key="sk-test",
        openai_model="gpt-4o-mini",
    )

    model = create_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4o-mini"


@pytest.mark.usefixtures("clean_settings_env")
def test_ollama_provider_creates_ollama_chat_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        ollama_model="llama3.2",
        ollama_base_url="http://localhost:11434",
    )

    model = create_chat_model(settings)

    assert isinstance(model, ChatOllama)
    assert model.model == "llama3.2"
    assert model.base_url == "http://localhost:11434"


@pytest.mark.usefixtures("clean_settings_env")
def test_openai_provider_without_api_key_raises_informative_error() -> None:
    settings = Settings(_env_file=None, llm_provider="openai")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_chat_model(settings)


@pytest.mark.usefixtures("clean_settings_env")
def test_openai_provider_with_empty_api_key_raises_error() -> None:
    settings = Settings(_env_file=None, llm_provider="openai", openai_api_key="")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_chat_model(settings)
