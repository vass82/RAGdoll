"""Application configuration loaded from environment variables and ``.env``."""

from enum import StrEnum
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    """Supported chat model providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Infrastructure settings for model and vector store selection.

    Values are read from environment variables (case-insensitive) and from a
    ``.env`` file in the working directory. Unknown variables are ignored.

    :ivar llm_provider: Which chat model provider to use (``openai`` or ``ollama``).
    :ivar openai_api_key: API key for OpenAI. Required when ``llm_provider`` is ``openai``.
    :ivar openai_model: OpenAI chat model name.
    :ivar ollama_base_url: Base URL of the local Ollama server.
    :ivar ollama_model: Ollama model name.
    :ivar embedding_model: Hugging Face / Sentence Transformers model name used
        for local embeddings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def get_settings() -> Settings:
    """Return the application settings, loading them once per process.

    :returns: The cached settings instance.
    :rtype: Settings
    """
    return Settings()
